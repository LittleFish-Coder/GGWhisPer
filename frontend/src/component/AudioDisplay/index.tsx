import { ReactElement, useEffect, useRef, useState } from "react";
import { downloadFile } from "../../api/fileDownload";
import "./index.scss";

type propsType = Readonly<{
    audio_id: number;
}>;
export default function AudioPlayer(props: propsType): ReactElement {
    const { audio_id } = props;

    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string>("");
    const [audioUrl_origin, setAudioUrl_Origin] = useState<string>("");
    const [audioUrl_zh, setAudioUrl_ZH] = useState<string>("");
    const [audioUrl_en, setAudioUrl_EN] = useState<string>("");
    const [audioUrl_ja, setAudioUrl_JA] = useState<string>("");
    const [audioUrl_de, setAudioUrl_DE] = useState<string>("");

    useEffect(() => {
        const fetchAudio = async () => {
            try {
                setIsLoading(true);
                setError("");

                const response_origin = await downloadFile(
                    audio_id,
                    "wav",
                    "wav"
                );
                if (!response_origin?.download_url) {
                    throw new Error("下載連結無效");
                }

                setAudioUrl_Origin(response_origin.download_url);

                const response_zh = await downloadFile(
                    audio_id,
                    "wav/zh",
                    "mp3"
                );
                if (!response_zh?.download_url) {
                    throw new Error("下載連結無效");
                }

                setAudioUrl_ZH(response_zh.download_url);

                const response_en = await downloadFile(
                    audio_id,
                    "wav/en",
                    "mp3"
                );
                if (!response_en?.download_url) {
                    throw new Error("下載連結無效");
                }

                setAudioUrl_EN(response_en.download_url);

                const response_ja = await downloadFile(
                    audio_id,
                    "wav/ja",
                    "mp3"
                );
                if (!response_ja?.download_url) {
                    throw new Error("下載連結無效");
                }

                setAudioUrl_JA(response_ja.download_url);

                const response_de = await downloadFile(
                    audio_id,
                    "wav/de",
                    "mp3"
                );
                if (!response_de?.download_url) {
                    throw new Error("下載連結無效");
                }

                setAudioUrl_DE(response_de.download_url);
            } catch (err) {
                setError("音頻加載失敗");
                console.error("Error fetching audio:", err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchAudio();

        return () => {
            if (audioUrl_origin) {
                URL.revokeObjectURL(audioUrl_origin);
            }
        };
    }, [audio_id]);

    if (isLoading) {
        return <div>載入音頻中...</div>;
    }

    if (error) {
        return <div style={{ color: "red" }}>{error}</div>;
    }

    return (
        <div id="audioDisplay">
            <p>原始音檔</p>
            <audio controls src={audioUrl_origin} style={{ width: "100%" }}>
                Your browser does not support the audio element.
            </audio>
            <p>中文音檔</p>
            <audio controls src={audioUrl_zh} style={{ width: "100%" }}>
                Your browser does not support the audio element.
            </audio>
            <p>英文音檔</p>
            <audio controls src={audioUrl_en} style={{ width: "100%" }}>
                Your browser does not support the audio element.
            </audio>
            <p>日文音檔</p>
            <audio controls src={audioUrl_ja} style={{ width: "100%" }}>
                Your browser does not support the audio element.
            </audio>
            <p>德文音檔</p>
            <audio controls src={audioUrl_de} style={{ width: "100%" }}>
                Your browser does not support the audio element.
            </audio>
        </div>
    );
}
