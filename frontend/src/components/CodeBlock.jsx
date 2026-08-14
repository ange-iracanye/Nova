import { useEffect, useState } from "react";
import { codeToHtml } from "shiki";

export default function CodeBlock({ language, code }) {

    const [html, setHtml] = useState("");

    useEffect(() => {

        let cancelled = false;

        async function highlight() {

            try {

                const result = await codeToHtml(code, {
                    lang: language || "text",
                    theme: "github-dark"
                });

                if (!cancelled) {
                    setHtml(result);
                }

            } catch {

                if (!cancelled) {
                    setHtml("");
                }

            }

        }

        highlight();

        return () => {
            cancelled = true;
        };

    }, [code, language]);

    if (!html) {

        return (
            <pre className="bg-gray-950 rounded-xl p-4 overflow-x-auto">
                <code>{code}</code>
            </pre>
        );

    }

    return (
        <div
            className="overflow-x-auto rounded-xl my-4"
            dangerouslySetInnerHTML={{
                __html: html
            }}
        />
    );
}