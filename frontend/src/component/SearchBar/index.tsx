import { ReactElement, useState, useCallback, ChangeEvent } from "react";
import "./index.scss";

interface SearchParams {
    start_date: string;
    end_date: string;
    title: string;
    info: string;
    term: string;
    transcript: string;
}

interface SearchBarProps {
    onSearch: (params: SearchParams) => void;
    onReset: () => void;
}

export default function SearchBar({
    onSearch,
    onReset,
}: SearchBarProps): ReactElement {
    const [searchParams, setSearchParams] = useState<SearchParams>({
        start_date: "",
        end_date: "",
        title: "",
        info: "",
        term: "",
        transcript: "",
    });

    const handleInputChange = useCallback(
        (e: ChangeEvent<HTMLInputElement>) => {
            const { name, value } = e.target;
            setSearchParams((prev) => ({
                ...prev,
                [name]: value,
            }));
        },
        []
    );

    const handleSearch = useCallback(() => {
        onSearch(searchParams);
    }, [onSearch, searchParams]);

    const handleReset = useCallback(() => {
        setSearchParams({
            start_date: "",
            end_date: "",
            title: "",
            info: "",
            term: "",
            transcript: "",
        });
        if (onReset) {
            onReset();
        }
    }, []);

    return (
        <div className="search-bar">
            <p>會議紀錄搜尋</p>
            <div className="search-row">
                <div className="search-field">
                    <label>開始日期：</label>
                    <input
                        type="date"
                        name="start_date"
                        value={searchParams.start_date}
                        onChange={handleInputChange}
                    />
                </div>
                <div className="search-field">
                    <label>結束日期：</label>
                    <input
                        type="date"
                        name="end_date"
                        value={searchParams.end_date}
                        onChange={handleInputChange}
                    />
                </div>
            </div>

            <div className="search-row">
                <div className="search-field">
                    <label>標題：</label>
                    <input
                        type="text"
                        name="title"
                        value={searchParams.title}
                        onChange={handleInputChange}
                        placeholder="搜尋標題"
                    />
                </div>
                <div className="search-field">
                    <label>描述：</label>
                    <input
                        type="text"
                        name="info"
                        value={searchParams.info}
                        onChange={handleInputChange}
                        placeholder="搜尋描述"
                    />
                </div>
            </div>

            <div className="search-row">
                <div className="search-field">
                    <label>逐字稿內文:</label>
                    <input
                        type="text"
                        name="transcript"
                        value={searchParams.transcript}
                        onChange={handleInputChange}
                        placeholder="搜尋逐字稿"
                    />
                </div>
            </div>

            <div className="search-row">
                <div className="search-field">
                    <label>專有名詞:</label>
                    <input
                        type="text"
                        name="term"
                        value={searchParams.term}
                        onChange={handleInputChange}
                        placeholder="搜尋專有名詞"
                    />
                </div>
            </div>

            <div className="button-group">
                <button className="search-button" onClick={handleSearch}>
                    搜尋
                </button>
                <button className="reset-button" onClick={handleReset}>
                    重置
                </button>
            </div>
        </div>
    );
}
