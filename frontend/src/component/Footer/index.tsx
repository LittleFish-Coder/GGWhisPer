import { ReactElement } from "react";

import "./index.scss";

export default function Footer(): ReactElement {
    return (
        <div id="footer">
            <div className="leftFooter">
                <h2>多語言翻譯溝通平台</h2>
                <p>
                    Copyright © TSMC - Taiwan Semiconductor Manufacturing
                    Company Limited, All Rights Reserved.
                </p>
            </div>

            <div className="rightFooter">
                <a href="https://www.tsmc.com/chinese/legal_and_trademark">
                    法律與商標
                </a>
                <a href="https://www.tsmc.com/chinese/privacy">隱私權聲明</a>
                <a href="https://www.tsmc.com/chinese/cookie">Cookie政策</a>
                <a href="https://www.tsmc.com/chinese/sitemap">網站地圖</a>
            </div>
        </div>
    );
}
