import { ReactElement, useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { postAudioWithFile, postAudio, updateAudio } from "../../api/audio";
import { doInference, getTerm, getTranscript } from "../../api/ai";
import { Audio } from "../../schema/audio";
import { RxCross2 } from "react-icons/rx";
import { useLoader } from "../../App";

import "./index.scss";

type propsType = Readonly<{
    onClose: () => void;
    now_type: string;
}>;

export default function AudioUploader(props: propsType): ReactElement {
    const { setIsLoading } = useLoader();
    const navigate = useNavigate();
    const { onClose, now_type } = props;
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState<string>("");
    const [info, setInfo] = useState<string>("");
    const [title, setTitle] = useState<string>("");
    const [filePath, setFilePath] = useState<string>("");

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file && file.type === "audio/wav") {
            setSelectedFile(file);
            setFilePath(file.name); // 暫時使用檔名作為 file_path
            setUploadStatus("");
        } else {
            setUploadStatus("請選擇 .wav 檔案");
            setSelectedFile(null);
            setFilePath("");
        }
    };

    const handleUpload = async () => {
        if (title.trim() === "" || info.trim() === "") {
            alert("標題和描述不能為空");
            return;
        }
        Close();
        if (now_type == "upload") {
            if (!selectedFile) {
                alert("請先選擇檔案");
                return;
            }

            setIsUploading(true);
            setIsLoading(true);

            const audio: Audio = {
                title: title,
                info: info,
                transcript: {},
                term: {},
            };

            try {
                const response = await postAudioWithFile(audio, selectedFile);

                if (response) {
                    audio.id = response.id;

                    // Step 2: Start inference
                    await doInference(audio.id || 0);

                    // Step 3: Get transcript and term data simultaneously
                    const [transcriptResponse, termResponse] =
                        await Promise.all([
                            getTranscript(audio.id || 0),
                            getTerm(audio.id || 0),
                        ]);
                    audio.transcript = transcriptResponse;
                    audio.term = termResponse;
                    await updateAudio(audio);

                    // Reset file input
                    setSelectedFile(null);
                    const fileInput = document.querySelector(
                        'input[type="file"]'
                    ) as HTMLInputElement;
                    if (fileInput) fileInput.value = "";
                }
            } catch (error) {
                // Error handlin
            } finally {
                setIsUploading(false);
                setIsLoading(false);
                navigate(`/audioContent/${audio.id}`);
            }
        } else {
            const audio: Audio = {
                title: title,
                info: info,
                transcript: {},
                term: {},
            };
            postAudio(audio)
                .then((data) => {
                    if (data) {
                        navigate(`/audioRecord/${data.id}`);
                    }
                })
                .catch((error) => {
                    if (error.response && error.response.status == 404) {
                    }
                });
        }
    };

    const Close = () => {
        onClose();
    };

    return (
        <div className="window">
            <div id="audioUploader">
                <button className="btn close-btn" onClick={Close}>
                    <RxCross2 />
                </button>

                <div className="above">
                    <div className="form-group">
                        <h2>標題</h2>
                        <input
                            type="text"
                            placeholder="請輸入標題"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                    </div>
                    {now_type == "upload" && (
                        <input
                            type="file"
                            accept=".wav"
                            onChange={handleFileChange}
                            disabled={isUploading}
                        />
                    )}
                </div>

                <div className="below">
                    <h2>描述</h2>
                    <textarea
                        placeholder="請輸入描述"
                        value={info}
                        onChange={(e) => setInfo(e.target.value)}
                    />
                </div>

                <div className="bottom">
                    <button className="post" onClick={handleUpload}>
                        {now_type === "upload" ? "上傳" : "開始錄製"}
                    </button>
                </div>
            </div>
        </div>
    );
}
