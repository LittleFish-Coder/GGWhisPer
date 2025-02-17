import { ReactElement, useState, useEffect } from "react";
import "./index.scss";
import { useSocket } from "../../context/socket";

interface TranscriptionResponse {
    type: string;
    raw_text: string;
    chinese: string;
    english: string;
    japanese: string;
    german: string;
    proper_nouns_chinese: string;
    proper_nouns_english: string;
    proper_nouns_japanese: string;
    proper_nouns_german: string;
}

interface TranscriptContent {
    raw_text: string;
    chinese: string;
    english: string;
    japanese: string;
    german: string;
}

interface Term {
    title: string;
    description: string;
}

interface TermLists {
    chinese: Term[];
    english: Term[];
    japanese: Term[];
    german: Term[];
}

const LANGUAGES = [
    { key: "raw_text", label: "原文" },
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

const parseTerm = (term: string): Term | null => {
    if (!term?.trim()) {
        return null;
    }

    const matches = term.match(/^(.+?)\s*\((.+?)\)$/);
    if (!matches) {
        return null;
    }

    return {
        title: matches[1].trim(),
        description: matches[2].trim(),
    };
};

const addTermIfUnique = (terms: Term[], newTerm: Term | null): Term[] => {
    if (!newTerm || terms.some((item) => item.title === newTerm.title)) {
        return terms;
    }
    return [...terms, newTerm];
};

export default function RecordTranscriptAndTerm(): ReactElement {
    const { socket, isConnected } = useSocket();

    const [currentTermIndex, setCurrentTermIndex] = useState(0);
    const [transcriptContents, setTranscriptContents] =
        useState<TranscriptContent>({
            raw_text: "",
            chinese: "",
            english: "",
            japanese: "",
            german: "",
        });
    const [termLists, setTermLists] = useState<TermLists>({
        chinese: [],
        english: [],
        japanese: [],
        german: [],
    });
    const [selectedLang, setSelectedLang] = useState("raw_text");

    useEffect(() => {
        if (!socket) return;

        socket.on("transcription_response", (data: TranscriptionResponse) => {
            setTranscriptContents((prev) => ({
                raw_text: prev.raw_text + "\n" + (data.raw_text || ""),
                chinese: prev.chinese + "\n" + (data.chinese || ""),
                english: prev.english + "\n" + (data.english || ""),
                japanese: prev.japanese + "\n" + (data.japanese || ""),
                german: prev.german + "\n" + (data.german || ""),
            }));

            const trimmedTerms = {
                chinese: parseTerm(data.proper_nouns_chinese?.trim() || ""),
                english: parseTerm(data.proper_nouns_english?.trim() || ""),
                japanese: parseTerm(data.proper_nouns_japanese?.trim() || ""),
                german: parseTerm(data.proper_nouns_german?.trim() || ""),
            };

            setTermLists((prev) => ({
                chinese: addTermIfUnique(prev.chinese, trimmedTerms.chinese),
                english: addTermIfUnique(prev.english, trimmedTerms.english),
                japanese: addTermIfUnique(prev.japanese, trimmedTerms.japanese),
                german: addTermIfUnique(prev.german, trimmedTerms.german),
            }));
        });

        socket.on("error", (error: string) => {
            console.error("Transcription error:", error);
        });

        return () => {
            socket.off("transcription_response");
            socket.off("error");
        };
    }, [socket]);

    const getCurrentTerm = () => {
        const currentLang = getSelectedLanguageKey();
        const terms = termLists[currentLang];
        if (terms.length === 0) return null;
        return terms[currentTermIndex];
    };

    const handlePrevTerm = () => {
        const terms = termLists[getSelectedLanguageKey()];
        setCurrentTermIndex((prev) => (prev > 0 ? prev - 1 : terms.length - 1));
    };

    const handleNextTerm = () => {
        const terms = termLists[getSelectedLanguageKey()];
        setCurrentTermIndex((prev) => (prev < terms.length - 1 ? prev + 1 : 0));
    };

    const getSelectedLanguageKey = (): keyof TermLists =>
        selectedLang === "raw_text"
            ? "english"
            : (selectedLang as keyof TermLists);

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
                    {transcriptContents[
                        selectedLang as keyof TranscriptContent
                    ] || "..."}
                </div>
            </div>
            <div className="terminology-container">
                <p className="terminology-term">
                    {TERM_LABELS[getSelectedLanguageKey()]}
                </p>
                <div className="term-navigation">
                    <button
                        onClick={handlePrevTerm}
                        className="nav-btn"
                        disabled={
                            termLists[
                                selectedLang === "raw_text"
                                    ? "english"
                                    : (selectedLang as keyof TermLists)
                            ].length === 0
                        }
                    ></button>

                    <div className="term-card">
                        {(() => {
                            const currentTerm = getCurrentTerm();
                            if (!currentTerm) return "";
                            return (
                                <>
                                    <div className="term-title">
                                        {currentTerm.title}
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
                        disabled={
                            termLists[
                                selectedLang === "raw_text"
                                    ? "english"
                                    : (selectedLang as keyof TermLists)
                            ].length === 0
                        }
                    ></button>
                </div>

                <div className="term-counter">
                    {termLists[
                        selectedLang === "raw_text"
                            ? "english"
                            : (selectedLang as keyof TermLists)
                    ].length > 0
                        ? `${currentTermIndex + 1} / ${
                              termLists[
                                  selectedLang === "raw_text"
                                      ? "english"
                                      : (selectedLang as keyof TermLists)
                              ].length
                          }`
                        : "0 / 0"}
                </div>
            </div>
        </div>
    );
}
