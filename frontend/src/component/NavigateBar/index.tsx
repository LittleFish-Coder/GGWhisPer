import { ReactElement } from "react";
import { Link } from "react-router-dom";
import logo from "../../asset/logo.png";

import "./index.scss";

export default function NavigateBar(): ReactElement {
    return (
        <div id="navigateBar">
            <Link to="/" className="title">
                <img src={logo} />
                <h1>GGWhisPer</h1>
            </Link>
        </div>
    );
}
