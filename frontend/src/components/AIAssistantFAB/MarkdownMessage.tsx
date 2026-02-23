import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Link } from 'react-router-dom';

interface MarkdownMessageProps {
    content: string;
    className?: string;
}

const isValidExternalUrl = (url: string): boolean => {
    if (!url) return false;
    const lower = url.toLowerCase();
    return (
        lower.startsWith('https://') ||
        lower.startsWith('http://') ||
        lower.startsWith('//') ||
        lower.startsWith('mailto:')
    );
};

/** Renderiza Markdown con enlaces internos y externos clicables. */
export function MarkdownMessage({ content, className }: MarkdownMessageProps) {
    return (
        <div className={className}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    a: ({ href, children }) => {
                        const url = href || '';
                        if (url.startsWith('/') && !url.startsWith('//')) {
                            return <Link to={url}>{children}</Link>;
                        }
                        if (isValidExternalUrl(url)) {
                            return (
                                <a href={url} target="_blank" rel="noopener noreferrer">
                                    {children}
                                </a>
                            );
                        }
                        return <span>{children}</span>;
                    },
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
