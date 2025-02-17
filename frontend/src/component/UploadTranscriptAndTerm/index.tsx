import { ReactElement, useState, useEffect } from "react";
import "./index.scss";
import { useLocation } from "react-router-dom";
import { Audio } from "../../schema/audio";

const LANGUAGES = [
    { key: "raw", label: "原文" },
    { key: "chinese", label: "中文" },
    { key: "english", label: "English" },
    { key: "japanese", label: "日本語" },
    { key: "german", label: "Deutsch" },
] as const;

const TERM_LABELS = {
    chinese: "專有名詞",
    english: "Proper noun",
    japanese: "こゆうめいし",
    german: "Eigenname",
} as const;

type TermItem = {
    term: string;
    description: string;
};

type TermData = {
    zh: TermItem[];
    en: TermItem[];
    ja: TermItem[];
    de: TermItem[];
};

const LANG_TO_TERM_KEY: Record<string, keyof TermData> = {
    chinese: "zh",
    english: "en",
    japanese: "ja",
    german: "de",
};

const TRANSCRIPT_LANG_MAP = {
    raw: "raw",
    chinese: "zh",
    english: "en",
    japanese: "ja",
    german: "de",
} as const;

type DisplayedTranscripts = {
    raw: string[];
    zh: string[];
    en: string[];
    ja: string[];
    de: string[];
};

type Props = {
    audio?: Audio;
};

export default function UploadTranscriptAndTerm({
    audio,
}: Props): ReactElement {
    const [currentTermIndex, setCurrentTermIndex] = useState(0);

    const [selectedLang, setSelectedLang] = useState("raw");
    const [displayedTranscripts, setDisplayedTranscripts] =
        useState<DisplayedTranscripts>({
            raw: [],
            zh: [],
            en: [],
            ja: [],
            de: [],
        });

    useEffect(() => {
        console.log(audio);
        if (!audio?.transcript) return;

        // 初始化所有語言的字幕陣列
        const newDisplayedTranscripts: DisplayedTranscripts = {
            raw: [],
            zh: [],
            en: [],
            ja: [],
            de: [],
        };

        Object.entries(TRANSCRIPT_LANG_MAP).forEach(([_, langKey]) => {
            const transcripts = audio.transcript[langKey] || [];
            // 加上明確的型別宣告
            newDisplayedTranscripts[langKey] = transcripts.filter(
                (text: string) => text?.trim()
            );
        });

        // 一次性設置所有字幕
        setDisplayedTranscripts(newDisplayedTranscripts);
    }, [audio]);

    const getCurrentTerm = () => {
        const termKey = LANG_TO_TERM_KEY[selectedLang];
        const terms = audio?.term?.[termKey] || [];
        if (terms.length === 0) return null;
        return terms[currentTermIndex];
    };

    const getTermsList = () => {
        const termKey = LANG_TO_TERM_KEY[selectedLang];
        return audio?.term?.[termKey] || [];
    };

    const handlePrevTerm = () => {
        const terms = getTermsList();
        setCurrentTermIndex((prev) => (prev > 0 ? prev - 1 : terms.length - 1));
    };

    const handleNextTerm = () => {
        const terms = getTermsList();
        setCurrentTermIndex((prev) => (prev < terms.length - 1 ? prev + 1 : 0));
    };

    return (
        <div className="transcript-layout">
            <div className="transcript-container">
                <div className="language-switcher">
                    {LANGUAGES.map((lang) => (
                        <button
                            key={lang.key}
                            onClick={() => setSelectedLang(lang.key)}
                            className={`lang-btn ${
                                selectedLang === lang.key
                                    ? "active"
                                    : "inactive"
                            }`}
                        >
                            {lang.label}
                        </button>
                    ))}
                </div>
                <div className="transcript-content">
                    {displayedTranscripts[
                        TRANSCRIPT_LANG_MAP[
                            selectedLang as keyof typeof TRANSCRIPT_LANG_MAP
                        ]
                    ].map((text, index) => (
                        <div key={index} className="transcript-line">
                            {text}
                        </div>
                    ))}
                </div>
            </div>
            <div className="terminology-container">
                <p className="terminology-term">
                    {
                        TERM_LABELS[
                            LANG_TO_TERM_KEY[selectedLang] === "de"
                                ? "german"
                                : LANG_TO_TERM_KEY[selectedLang] === "en"
                                ? "english"
                                : LANG_TO_TERM_KEY[selectedLang] === "ja"
                                ? "japanese"
                                : "chinese"
                        ]
                    }
                </p>
                <div className="term-navigation">
                    <button
                        onClick={handlePrevTerm}
                        className="nav-btn"
                        disabled={getTermsList().length === 0}
                    ></button>

                    <div className="term-card">
                        {(() => {
                            const currentTerm = getCurrentTerm();
                            if (!currentTerm) return "";
                            return (
                                <>
                                    <div className="term-title">
                                        {currentTerm.term}
                                    </div>
                                    <div className="term-description">
                                        {currentTerm.description}
                                    </div>
                                </>
                            );
                        })()}
                    </div>

                    <button
                        onClick={handleNextTerm}
                        className="nav-btn"
                        disabled={getTermsList().length === 0}
                    ></button>
                </div>

                <div className="term-counter">
                    {(() => {
                        const terms = getTermsList();
                        return terms.length > 0
                            ? `${currentTermIndex + 1} / ${terms.length}`
                            : "0 / 0";
                    })()}
                </div>
            </div>
        </div>
    );
}
