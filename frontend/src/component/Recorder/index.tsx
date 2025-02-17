import React, { useState, useEffect, useRef } from "react";
import { ReactMic } from "react-mic";
import { Mic, MicOff, Save } from "lucide-react";
import "./index.scss";
import { useSocket } from "../../context/socket";
import { uploadAudio } from "../../api/fileUpload";
import { Link, useParams, useNavigate } from "react-router-dom";
import { doInference, getTerm, getTranscript } from "../../api/ai";
import { updateAudio } from "../../api/audio";
import { Audio } from "../../schema/audio";
import { useLoader } from "../../App";

type PropsType = Readonly<{
    onStop?: (recordedBlob: Blob) => void;
}>;

export default function Recorder({ onStop }: PropsType) {
    const navigate = useNavigate();
    const { isLoading, setIsLoading } = useLoader();
    const { socket, isConnected } = useSocket();
    const params = useParams();

    const [isInferencing, setIsInferencing] = useState(false);

    // State management
    const [isRecording, setIsRecording] = useState(false);
    const [isDisabled, setIsDisabled] = useState(false);
    const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
    const [recordingTime, setRecordingTime] = useState(0);
    const [audioURL, setAudioURL] = useState<string>("");

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioStreamRef = useRef<MediaStream | null>(null);

    // 改進的音頻流處理
    useEffect(() => {
        let audioContext: AudioContext | null = null;
        let scriptProcessor: ScriptProcessorNode | null = null;
        let dataTimer: NodeJS.Timeout | null = null;

        const setupAudioStream = async () => {
            try {
                if (!isConnected || !isRecording) return;

                const stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        channelCount: 1,
                        sampleRate: 44100,
                    },
                });
                audioStreamRef.current = stream;

                audioContext = new AudioContext({ sampleRate: 44100 });
                const source = audioContext.createMediaStreamSource(stream);
                scriptProcessor = audioContext.createScriptProcessor(
                    4096,
                    1,
                    1
                );

                source.connect(scriptProcessor);
                scriptProcessor.connect(audioContext.destination);

                let buffer: Float32Array[] = [];
                let totalSamples = 0;
                let lastSendTime = Date.now();

                scriptProcessor.onaudioprocess = (e) => {
                    const inputData = e.inputBuffer.getChannelData(0);
                    buffer.push(new Float32Array(inputData));
                    totalSamples += inputData.length;

                    const currentTime = Date.now();
                    if (
                        currentTime - lastSendTime >= 3000 &&
                        buffer.length > 0
                    ) {
                        sendAudioData(buffer, totalSamples);
                        lastSendTime = currentTime;
                        buffer = [];
                        totalSamples = 0;
                    }
                };
            } catch (error) {
                console.error("Error setting up audio stream:", error);
                setIsRecording(false);
            }
        };

        const sendAudioData = (
            buffer: Float32Array[],
            totalSamples: number
        ) => {
            if (!socket?.connected) return;
            try {
                // 合併緩衝區數據
                const mergedBuffer = new Float32Array(totalSamples);
                let offset = 0;
                for (const chunk of buffer) {
                    mergedBuffer.set(chunk, offset);
                    offset += chunk.length;
                }

                // 轉換為 16 位 PCM 數據
                const int16Data = new Int16Array(mergedBuffer.length);
                for (let j = 0; j < mergedBuffer.length; j++) {
                    const s = Math.max(-1, Math.min(1, mergedBuffer[j]));
                    int16Data[j] = s < 0 ? s * 0x8000 : s * 0x7fff;
                }

                // 創建固定的 WAV 文件頭
                const wavHeader = new Uint8Array([
                    // RIFF chunk
                    "R".charCodeAt(0),
                    "I".charCodeAt(0),
                    "F".charCodeAt(0),
                    "F".charCodeAt(0),
                    0x24,
                    0x65,
                    0x04,
                    0x00, // Chunk size (依據您提供的示例)

                    // WAVE header
                    "W".charCodeAt(0),
                    "A".charCodeAt(0),
                    "V".charCodeAt(0),
                    "E".charCodeAt(0),

                    // fmt chunk
                    "f".charCodeAt(0),
                    "m".charCodeAt(0),
                    "t".charCodeAt(0),
                    " ".charCodeAt(0),
                    0x10,
                    0x00,
                    0x00,
                    0x00, // Subchunk1Size
                    0x01,
                    0x00, // Audio format (PCM)
                    0x01,
                    0x00, // Number of channels
                    0x80,
                    0xbb,
                    0x00,
                    0x00, // Sample rate (48000 Hz)
                    0x00,
                    0x77,
                    0x01,
                    0x00, // Byte rate
                    0x02,
                    0x00, // Block align
                    0x10,
                    0x00, // Bits per sample

                    // data chunk
                    "d".charCodeAt(0),
                    "a".charCodeAt(0),
                    "t".charCodeAt(0),
                    "a".charCodeAt(0),
                ]);

                // 創建完整的音訊數據
                const audioBytes = new Uint8Array(int16Data.buffer);
                const messageData = new Uint8Array(
                    wavHeader.length + audioBytes.length
                );

                // 組合 WAV 文件頭和音訊數據
                messageData.set(wavHeader, 0);
                messageData.set(audioBytes, wavHeader.length);

                // 發送數據
                if (socket?.connected) {
                    socket.emit("audio_data", messageData);
                }
            } catch (error) {
                console.error("Error processing audio data:", error);
            }
        };

        // ... 其餘代碼保持不變 ...

        if (isRecording && isConnected) {
            setupAudioStream();
        }

        return () => {
            if (dataTimer) clearInterval(dataTimer);
            if (scriptProcessor) {
                scriptProcessor.disconnect();
            }
            if (audioStreamRef.current) {
                audioStreamRef.current
                    .getTracks()
                    .forEach((track) => track.stop());
                audioStreamRef.current = null;
            }
            if (audioContext) {
                audioContext.close();
            }
        };
    }, [isRecording, isConnected, socket]);

    // Timer for recording duration
    useEffect(() => {
        let timer: NodeJS.Timeout | null = null;

        if (isRecording) {
            timer = setInterval(() => {
                setRecordingTime((prev) => prev + 1);
            }, 1000);
        }

        return () => {
            if (timer) clearInterval(timer);
        };
    }, [isRecording]);

    const handleStartRecording = () => {
        if (!isConnected) {
            console.warn("Socket not connected. Cannot start recording.");
            return;
        }
        setIsRecording(!isRecording);
        if (!isRecording) {
            setRecordingTime(0);
        }
    };

    const convertToWav = async (audioBlob: Blob): Promise<Blob> => {
        const audioContext = new AudioContext();
        const arrayBuffer = await audioBlob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        const length = audioBuffer.length;

        // 使用固定的配置
        const numberOfChannels = 1; // 固定為單聲道
        const sampleRate = 48000; // 固定為 48000 Hz
        const bitsPerSample = 16; // 固定為 16 bits
        const byteRate = sampleRate * numberOfChannels * (bitsPerSample / 8);
        const blockAlign = numberOfChannels * (bitsPerSample / 8);

        const buffer = new ArrayBuffer(44 + length * 2);
        const view = new DataView(buffer);

        // WAV Header
        // RIFF chunk
        view.setUint8(0, "R".charCodeAt(0));
        view.setUint8(1, "I".charCodeAt(0));
        view.setUint8(2, "F".charCodeAt(0));
        view.setUint8(3, "F".charCodeAt(0));

        // Chunk size (0x246504)
        view.setUint8(4, 0x24);
        view.setUint8(5, 0x65);
        view.setUint8(6, 0x04);
        view.setUint8(7, 0x00);

        // WAVE header
        view.setUint8(8, "W".charCodeAt(0));
        view.setUint8(9, "A".charCodeAt(0));
        view.setUint8(10, "V".charCodeAt(0));
        view.setUint8(11, "E".charCodeAt(0));

        // fmt chunk
        view.setUint8(12, "f".charCodeAt(0));
        view.setUint8(13, "m".charCodeAt(0));
        view.setUint8(14, "t".charCodeAt(0));
        view.setUint8(15, " ".charCodeAt(0));

        // Subchunk1Size (16)
        view.setUint8(16, 0x10);
        view.setUint8(17, 0x00);
        view.setUint8(18, 0x00);
        view.setUint8(19, 0x00);

        // Audio format (PCM = 1)
        view.setUint8(20, 0x01);
        view.setUint8(21, 0x00);

        // Number of channels (1)
        view.setUint8(22, 0x01);
        view.setUint8(23, 0x00);

        // Sample rate (48000 Hz = 0xbb80)
        view.setUint8(24, 0x80);
        view.setUint8(25, 0xbb);
        view.setUint8(26, 0x00);
        view.setUint8(27, 0x00);

        // Byte rate (0x17700)
        view.setUint8(28, 0x00);
        view.setUint8(29, 0x77);
        view.setUint8(30, 0x01);
        view.setUint8(31, 0x00);

        // Block align (2)
        view.setUint8(32, 0x02);
        view.setUint8(33, 0x00);

        // Bits per sample (16)
        view.setUint8(34, 0x10);
        view.setUint8(35, 0x00);

        // data chunk
        view.setUint8(36, "d".charCodeAt(0));
        view.setUint8(37, "a".charCodeAt(0));
        view.setUint8(38, "t".charCodeAt(0));
        view.setUint8(39, "a".charCodeAt(0));

        // data size
        const dataSize = length * 2;
        view.setUint32(40, dataSize, true);

        // 寫入音頻數據
        const channelData = audioBuffer.getChannelData(0);
        let offset = 44;
        for (let i = 0; i < length; i++) {
            const sample = Math.max(-1, Math.min(1, channelData[i]));
            view.setInt16(
                offset,
                sample < 0 ? sample * 0x8000 : sample * 0x7fff,
                true
            );
            offset += 2;
        }

        return new Blob([buffer], { type: "audio/wav" });
    };

    const handleStop = async (recordedBlob: any) => {
        try {
            console.log("Recording stopped, processing...");
            const wavBlob = await convertToWav(recordedBlob.blob);
            setRecordedBlob(wavBlob);
            const url = URL.createObjectURL(wavBlob);
            setAudioURL(url);
            onStop?.(wavBlob);

            try {
                setIsInferencing(true);
                await uploadAudio(
                    Number(params.audioId) || 0,
                    "wav",
                    "wav",
                    wavBlob
                );
                setIsDisabled(true);
                doInference(Number(params.audioId) || 0);

                const audio: Audio = {
                    id: Number(params.audioId) || 0,
                    transcript: {},
                    term: {},
                };
                const [transcriptResponse, termResponse] = await Promise.all([
                    getTranscript(audio.id || 0),
                    getTerm(audio.id || 0),
                ]);
                audio.transcript = transcriptResponse;
                audio.term = termResponse;
                await updateAudio(audio);
                setIsInferencing(false);
            } catch (error) {
                console.error("Error uploading audio:", error);
                alert("上傳失敗，請重試");
            }
        } catch (error) {
            console.error("Error handling stop:", error);
        }
    };

    useEffect(() => {
        if (!isInferencing && isLoading) {
            setIsLoading(false);
            navigate(`/audioContent/${Number(params.audioId) || 0}`);
        }
    }, [isInferencing]);

    const handleSave = async () => {
        if (isInferencing) {
            setIsLoading(true);
        }
    };

    const formatTime = (seconds: number) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
    };

    return (
        <div className="recorder">
            <div className="recorder__controls">
                <button
                    onClick={handleStartRecording}
                    className={`recorder__button ${
                        isRecording ? "recorder__button--recording" : ""
                    }`}
                    disabled={isDisabled || !isConnected}
                >
                    {isRecording ? (
                        <MicOff className="recorder__icon" />
                    ) : (
                        <Mic className="recorder__icon" />
                    )}
                </button>
            </div>
            <div className="recorder_info">
                <div className="recorder__time">
                    {formatTime(recordingTime)}
                </div>
                <div className="recorder__status">
                    {isDisabled
                        ? ""
                        : !isConnected
                        ? "等待連接伺服器..."
                        : isRecording
                        ? "錄音中..."
                        : recordedBlob
                        ? ""
                        : "點擊即開始錄音"}
                </div>
            </div>

            <ReactMic
                record={isRecording}
                onStop={handleStop}
                mimeType="audio/wav"
                className="recorder__visualizer"
            />

            {recordedBlob && !isRecording && (
                <>
                    <audio
                        src={audioURL}
                        controls
                        className="recorder__audio"
                    />
                    <button
                        className="recorder__button recorder__button--save"
                        onClick={handleSave}
                    >
                        <Save className="recorder__icon" />
                    </button>
                    <p className="finish">錄製完成，建立檔案</p>
                </>
            )}
        </div>
    );
}
