import { ReactElement } from "react";
import loaderGif from "../../asset/loader.gif";
import "./index.scss";

export default function Loader(): ReactElement {
    return (
        <div id="loader">
            <img src={loaderGif} alt="Loading..." />
            <p>資訊處理中，請稍候</p>
        </div>
    );
}
