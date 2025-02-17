// ChatBot/index.tsx
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
import { IoChatbubbleEllipsesOutline } from "react-icons/io5";
import { IoClose, IoSend } from "react-icons/io5";
import "./index.scss";
import { getReply } from "../../api/ai";

interface Message {
    text: string;
    isBot: boolean;
    timestamp: Date;
}

export default function ChatBot(): ReactElement {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [chatbotReply, setChatbotReply] = useState("");

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const toggleChat = () => {
        setIsOpen(!isOpen);
        if (!isOpen) {
            // 開啟聊天室時顯示歡迎訊息
            if (messages.length === 0) {
                setMessages([
                    {
                        text: "你好！本系統專注於提供即時翻譯與專有名詞優化，我們將盡力提供最佳回答！",
                        isBot: true,
                        timestamp: new Date(),
                    },
                ]);
            }
        }
    };

    const handleSend = async () => {
        if (inputText.trim()) {
            // 添加使用者訊息
            setMessages((prev) => [
                ...prev,
                {
                    text: inputText,
                    isBot: false,
                    timestamp: new Date(),
                },
            ]);

            try {
                // 等待取得回覆
                const data = await getReply(inputText);

                setChatbotReply(data.reply);
                console.log(data.reply);

                // 先加入主要回覆
                setMessages((prev) => [
                    ...prev,
                    {
                        text: data.reply,
                        isBot: true,
                        timestamp: new Date(),
                    },
                ]);

                if (!data.term) {
                    setMessages((prev) => [
                        ...prev,
                        {
                            text: "本系統專注於提供即時翻譯與專有名詞優化，若您的問題與企業內部溝通、技術詞彙翻譯、跨語言協作有關，請再試一次，我們將盡力提供最佳回答！\n\n",
                            isBot: true,
                            timestamp: new Date(),
                        },
                    ]);
                }
            } catch (error) {
                console.error("Error getting reply:", error);
                // 可以在這裡處理錯誤情況
            }

            setInputText("");
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="chatBot">
            {isOpen && (
                <div className="chatWindow">
                    <div className="chatHeader">
                        <h2>專有名詞小字典</h2>
                        <button className="closeButton" onClick={toggleChat}>
                            <IoClose />
                        </button>
                    </div>
                    <div className="messagesContainer">
                        {messages.map((message, index) => (
                            <div
                                key={index}
                                className={`message ${
                                    message.isBot ? "bot" : "user"
                                }`}
                            >
                                <div className="messageContent">
                                    {message.text}
                                </div>
                                <div className="messageTime">
                                    {message.timestamp.toLocaleTimeString()}
                                </div>
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* 輸入區域 */}
                    <div className="inputArea">
                        <textarea
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="請輸入訊息..."
                            rows={1}
                        />
                        <button
                            className="sendButton"
                            onClick={handleSend}
                            disabled={!inputText.trim()}
                        >
                            <IoSend />
                        </button>
                    </div>
                </div>
            )}

            {/* 聊天按鈕 */}
            <button
                className={`chatButton ${isOpen ? "active" : ""}`}
                onClick={toggleChat}
            >
                <IoChatbubbleEllipsesOutline />
            </button>
        </div>
    );
}
