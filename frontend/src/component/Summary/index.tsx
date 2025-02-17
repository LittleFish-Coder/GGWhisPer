import { ReactElement, useState, useEffect } from "react";

import "./index.scss";

type propsType = Readonly<{
    content: string;
    start: boolean;
}>;

export default function Summary(props: propsType): ReactElement {
    const { content, start } = props;
    const [isLoading, setIsLoading] = useState<boolean>(false);

    useEffect(() => {
        if (start) {
            setIsLoading(true);
        }
    }, [start]);

    const parseContent = (text: string) => {
        const lines = text.split("\n");
        const parsedContent: JSX.Element[] = [];
        let currentList: string[] = [];
        let currentTable: string[][] = [];
        let isInTable = false;

        lines.forEach((line, index) => {
            const trimmedLine = line.trim();

            // 處理分隔線
            if (trimmedLine.startsWith("---")) {
                if (currentList.length > 0) {
                    parsedContent.push(
                        <ul
                            key={`list-${index}`}
                            className="list-disc pl-5 space-y-2 mb-4"
                        >
                            {currentList.map((item, i) => (
                                <li key={i} className="text-gray-700">
                                    {item.trim()}
                                </li>
                            ))}
                        </ul>
                    );
                    currentList = [];
                }
                parsedContent.push(
                    <hr key={`hr-${index}`} className="my-4 border-gray-300" />
                );
                return;
            }

            // 處理表格
            if (trimmedLine.startsWith("|")) {
                if (!isInTable) {
                    isInTable = true;
                    if (currentList.length > 0) {
                        parsedContent.push(
                            <ul
                                key={`list-${index}`}
                                className="list-disc pl-5 space-y-2 mb-4"
                            >
                                {currentList.map((item, i) => (
                                    <li key={i} className="text-gray-700">
                                        {item.trim()}
                                    </li>
                                ))}
                            </ul>
                        );
                        currentList = [];
                    }
                }
                const cells = trimmedLine
                    .split("|")
                    .filter((cell) => cell.trim() !== "")
                    .map((cell) => cell.trim());

                if (cells.length > 0) {
                    currentTable.push(cells);
                }
                return;
            } else if (isInTable) {
                // 表格結束，渲染表格
                if (currentTable.length > 0) {
                    const [headers, ...rows] = currentTable;
                    parsedContent.push(
                        <div
                            key={`table-${index}`}
                            className="overflow-x-auto mb-4"
                        >
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        {headers.map((header, i) => (
                                            <th
                                                key={i}
                                                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                                            >
                                                {header}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {rows.map((row, rowIndex) => (
                                        <tr key={rowIndex}>
                                            {row.map((cell, cellIndex) => (
                                                <td
                                                    key={cellIndex}
                                                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                                                >
                                                    {cell}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    );
                    currentTable = [];
                    isInTable = false;
                }
            }

            // 處理標題 (###)
            if (trimmedLine.startsWith("###")) {
                if (currentList.length > 0) {
                    parsedContent.push(
                        <ul
                            key={`list-${index}`}
                            className="list-disc pl-5 space-y-2 mb-4"
                        >
                            {currentList.map((item, i) => (
                                <li key={i} className="text-gray-700">
                                    {item.trim()}
                                </li>
                            ))}
                        </ul>
                    );
                    currentList = [];
                }
                parsedContent.push(
                    <h3
                        key={`heading-${index}`}
                        className="text-xl font-bold mb-4 mt-6"
                    >
                        {trimmedLine.replace("###", "").trim()}
                    </h3>
                );
            }
            // 處理一般段落和列表項
            else if (trimmedLine && !trimmedLine.startsWith("---")) {
                if (trimmedLine.match(/^\d+\./)) {
                    // 數字列表項
                    currentList.push(trimmedLine.replace(/^\d+\./, ""));
                } else if (trimmedLine.startsWith("*")) {
                    // 星號列表項
                    currentList.push(trimmedLine.substring(1));
                } else if (trimmedLine) {
                    // 一般段落
                    if (currentList.length > 0) {
                        parsedContent.push(
                            <ul
                                key={`list-${index}`}
                                className="list-disc pl-5 space-y-2 mb-4"
                            >
                                {currentList.map((item, i) => (
                                    <li key={i} className="text-gray-700">
                                        {item.trim()}
                                    </li>
                                ))}
                            </ul>
                        );
                        currentList = [];
                    }
                    parsedContent.push(
                        <p
                            key={`paragraph-${index}`}
                            className="mb-4 text-gray-700"
                        >
                            {trimmedLine}
                        </p>
                    );
                }
            }
        });

        // 處理最後的列表項
        if (currentList.length > 0) {
            parsedContent.push(
                <ul key="final-list" className="list-disc pl-5 space-y-2 mb-4">
                    {currentList.map((item, i) => (
                        <li key={i} className="text-gray-700">
                            {item.trim()}
                        </li>
                    ))}
                </ul>
            );
        }

        // 處理最後的表格
        if (currentTable.length > 0) {
            const [headers, ...rows] = currentTable;
            parsedContent.push(
                <div key="final-table" className="overflow-x-auto mb-4">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                {headers.map((header, i) => (
                                    <th
                                        key={i}
                                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                                    >
                                        {header}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {rows.map((row, rowIndex) => (
                                <tr key={rowIndex}>
                                    {row.map((cell, cellIndex) => (
                                        <td
                                            key={cellIndex}
                                            className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                                        >
                                            {cell}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            );
        }
        parsedContent.push(<br></br>);

        return parsedContent;
    };
    return (
        <div id="summary">
            {!content && isLoading ? (
                <div className="spinner-container">
                    <div className="spinner"></div>
                </div>
            ) : (
                <div className="markdown">{parseContent(content)}</div>
            )}
        </div>
    );
}
