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
import { Link, useNavigate } from "react-router-dom";
import "./index.scss";
import AudioUploader from "../../component/UploadAudio";
import { Audio } from "../../schema/audio";
import { IoMdAddCircle } from "react-icons/io";
import { getAudioList, searchAudio } from "../../api/audio";
import SearchBar from "../../component/SearchBar";
import { useLoader } from "../../App";

interface SearchParams {
    start_date: string;
    end_date: string;
    title: string;
    info: string;
    term: string;
    transcript: string;
}

export default function MainPage(): ReactElement {
    const { isLoading, setIsLoading } = useLoader();
    const navigate = useNavigate();

    const [openUploader, setOpenUploader] = useState<boolean>(false);
    const [now_type, setNowType] = useState<string>("record");
    const [audioList, setAudioList] = useState<Array<Audio>>([]);

    useEffect(() => {
        handleAudioList();
    }, []);

    const handleAudioList = () => {
        getAudioList().then((data) => {
            console.log(data); // Log the fetched diary list
            setAudioList(data);
        });
    };

    const openRecord = () => {
        setNowType("record");
        Open();
    };

    const openUpload = () => {
        setNowType("upload");
        Open();
    };

    const Open = () => {
        setOpenUploader(true);
    };
    const Close = () => {
        setOpenUploader(false);
    };

    const setTimeString = (release_time: string): string => {
        // If release_time is empty, set it to today's date
        if (release_time == "") {
            release_time = new Date().toISOString();
        }
        const releaseDate = new Date(release_time);
        const formattedDate = `${releaseDate.getFullYear()} / ${
            releaseDate.getMonth() + 1
        } / ${releaseDate.getDate()} ${releaseDate.getHours()}:${String(
            releaseDate.getMinutes()
        ).padStart(2, "0")}`;
        return formattedDate;
    };

    const handleSearch = async (params: SearchParams) => {
        try {
            console.log("搜尋參數：", params);
            const results = await searchAudio(params);
            console.log(results);
            setAudioList(results); // 使用搜尋結果更新列表
        } catch (error) {
            console.error("搜尋失敗：", error);
            // 可以加入錯誤處理，例如顯示錯誤訊息
        }
    };

    // 增加一個重置列表的函數
    const resetList = async () => {
        try {
            const data = await getAudioList();
            setAudioList(data);
        } catch (error) {
            console.error("重置列表失敗：", error);
        }
    };

    return (
        <>
            {/* 遮罩層 */}
            {(openUploader || isLoading) && (
                <div className="overlay" onClick={Close}></div>
            )}
            <div id="mainPage">
                <div className="buttons">
                    <button className="uploadButton" onClick={openUpload}>
                        <IoMdAddCircle className="addButton" />
                    </button>
                    <p>上傳音檔</p>
                    <button className="uploadButton" onClick={openRecord}>
                        <IoMdAddCircle className="addButton" />
                    </button>
                    <p>錄製音檔</p>
                </div>
                <SearchBar onSearch={handleSearch} onReset={resetList} />
                <div className="audioList">
                    {audioList.map((audio) => (
                        <Link key={audio.id} to={`./audioContent/${audio.id}`}>
                            <div className="audioItem">
                                <h3>{audio.title}</h3>
                                <span>
                                    {setTimeString(audio?.uploaded_date || "")}
                                </span>
                            </div>
                        </Link>
                    ))}
                </div>
                {openUploader && (
                    <AudioUploader onClose={Close} now_type={now_type} />
                )}
            </div>
        </>
    );
}
