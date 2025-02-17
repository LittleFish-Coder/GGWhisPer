import {
    CSSProperties,
    Dispatch,
    ReactElement,
    SetStateAction,
    useContext,
    useRef,
    useState,
    useEffect,
} from "react";
import { Link, useParams } from "react-router-dom";
import { IoMdDownload } from "react-icons/io";
import "./index.scss";
import { getSummary } from "../../api/ai";
import Summary from "../../component/Summary";
import RecordTranscriptAndTerm from "../../component/RecordTranscriptAndTerm";
import Recorder from "../../component/Recorder";
import { downloadFile } from "../../api/fileDownload";
import { MdSummarize } from "react-icons/md";
import axios from "axios";
import { postAudio, getAudio } from "../../api/audio";
import { Audio } from "../../schema/audio";

interface DownloadOption {
    label: string;
    dir: string;
    file_type: string;
}

export default function AudioRecordPage(): ReactElement {
    const params = useParams();

    const [summary, setSummary] = useState<string>("");
    const [startSummarize, setStartSummarize] = useState<boolean>(false);

    const [audio, setAudio] = useState<Audio>();
    const [selectedOption, setSelectedOption] = useState<string>("");

    useEffect(() => {
        getAudio(Number(params.audioId) || 0).then((data) => {
            setAudio(data);
        });
    }, []);

    const downloadOptions = (): DownloadOption[] => [
        {
            label: "中文逐字稿",
            dir: "transcript/zh",
            file_type: "txt",
        },
        {
            label: "英文逐字稿",
            dir: "transcript/en",
            file_type: "txt",
        },
        {
            label: "日文逐字稿",
            dir: "transcript/ja",
            file_type: "txt",
        },
        {
            label: "德文逐字稿",
            dir: "transcript/de",
            file_type: "txt",
        },
        {
            label: "中文專有名詞",
            dir: "term/zh",
            file_type: "txt",
        },
        {
            label: "英文專有名詞",
            dir: "term/en",
            file_type: "txt",
        },
        {
            label: "日文專有名詞",
            dir: "term/ja",
            file_type: "txt",
        },
        {
            label: "德文專有名詞",
            dir: "term/de",
            file_type: "txt",
        },
        {
            label: "中文總結",
            dir: "summary/zh",
            file_type: "md",
        },
    ];

    const handleDownload = (dir: string, file_type: string, label: string) => {
        downloadFile(Number(params.audioId) || 0, dir, file_type)
            .then((response) => {
                if (!response?.download_url) {
                    throw new Error("下載連結無效");
                }

                // 使用 axios 獲取文件內容
                return axios.get(response.download_url, {
                    responseType: "blob",
                    headers: {
                        Accept: "*/*",
                    },
                });
            })
            .then((response) => {
                // 創建 blob URL
                const blob = new Blob([response.data], {
                    type: file_type === "md" ? "text/markdown" : "text/plain",
                });
                const url = window.URL.createObjectURL(blob);

                // 創建下載連結
                const a = document.createElement("a");
                a.href = url;
                a.download = `${
                    Number(params.audioId) || 0
                }_${label}.${file_type}`;
                a.style.display = "none";
                document.body.appendChild(a);
                a.click();

                // 清理
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            })
            .catch((error) => {
                console.error("Download failed:", error);
                if (axios.isAxiosError(error)) {
                } else {
                }
            })
            .finally(() => {});
    };

    const handleSummary = () => {
        if (startSummarize) return;
        setStartSummarize(true);
        getSummary(Number(params.audioId) || 0)
            .then((data) => {
                setSummary(data.markdown);
            })
            .catch((error) => {
                if (error.response && error.response.status == 404) {
                }
            });
    };

    return (
        <div id="audioRecordPage">
            <div className="leftSide">
                <div className="leftSideAbove">
                    <h1 className="title">{audio?.title}</h1>
                    <p className="info">{audio?.info}</p>
                </div>
                <Recorder />
                <RecordTranscriptAndTerm />
            </div>
            <div className="rightSide">
                <div className="rightSideAbove">
                    <button
                        onClick={handleSummary}
                        className="summaryButton"
                        disabled={startSummarize}
                    >
                        <MdSummarize />
                    </button>

                    <p>生成總結</p>

                    {
                        <label className="dropdownMenu">
                            <IoMdDownload className="icon" />
                            <input type="checkbox" />
                            <div
                                className="mask"
                                style={{ "--length": 9 } as CSSProperties}
                            >
                                <div className="content body-bold">
                                    {downloadOptions().map((option, i) => (
                                        <div
                                            key={i}
                                            onClick={() =>
                                                handleDownload(
                                                    option.dir,
                                                    option.file_type,
                                                    option.label
                                                )
                                            }
                                        >
                                            <p>{option.label}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </label>
                    }
                    <p>檔案下載</p>
                </div>

                <Summary content={summary} start={startSummarize} />
            </div>
        </div>
    );
}
