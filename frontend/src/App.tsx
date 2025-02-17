import React, { createContext, useContext, useState } from "react";
import "./App.css";
import MainPage from "./view/MainPage";
import NavigateBar from "./component/NavigateBar";
import Footer from "./component/Footer";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import ChatBot from "./component/ChatBot";
import AudioInfoPage from "./view/AudioInfoPage";
import AudioRecordPage from "./view/AudioRecordPage";
import Loader from "./component/Loader";
import { SocketProvider } from "./context/socket";

export const LoaderContext = createContext({
    isLoading: false,
    setIsLoading: (loading: boolean) => {},
});

// 創建自定義 Hook 來使用 Loader
export const useLoader = () => {
    const context = useContext(LoaderContext);
    if (!context) {
        throw new Error("useLoader must be used within a LoaderProvider");
    }
    return context;
};

function App() {
    const [isLoading, setIsLoading] = useState(false);
    return (
        <LoaderContext.Provider value={{ isLoading, setIsLoading }}>
            <SocketProvider>
                <div className="App">
                    <NavigateBar />
                    {isLoading && <Loader />}
                    <Routes>
                        <Route path="/" element={<MainPage />} />
                        <Route path="*" element={<Navigate to="/" />} />
                        <Route
                            path="/audioContent/:audioId"
                            element={<AudioInfoPage />}
                        />
                        <Route
                            path="/audioRecord/:audioId"
                            element={<AudioRecordPage />}
                        />
                    </Routes>
                    <ChatBot />
                    <Footer />
                </div>
            </SocketProvider>
        </LoaderContext.Provider>
    );
}

export default App;
