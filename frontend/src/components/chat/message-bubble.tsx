import * as React from 'react';
import { cn } from '@/lib/utils';
import { AgentId } from '@/lib/agents-config';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FileText, ChevronDown, ChevronUp } from 'lucide-react';

export interface ChatDocument {
  id: number;
  text: string;
  source: string;
  score: number;
}

export interface MessageProps {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentId?: AgentId;
  documents?: ChatDocument[];
  sources?: string[];
}

interface MessageBubbleProps {
  message: MessageProps;
  onDocumentClick?: (doc: ChatDocument) => void;
}

export function MessageBubble({ message, onDocumentClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [isExpanded, setIsExpanded] = React.useState(false);
  
  // Pre-process content to handle custom citations like 【0](url)】 or [0](url)]
  // We make it standard markdown link: [0](url)
  const processedContent = message.content
    .replace(/【(\d+)\]\((.*?)\)】/g, '[$1]($2)')
    .replace(/\[(\d+)\]\((.*?)\)\]/g, '[$1]($2)');

  const renderMarkdown = () => (
    <ReactMarkdown 
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ node, ...props }) => {
          const isCitation = !isNaN(Number(props.children)) && props.href;
          if (isCitation) {
            return (
              <a
                href={`#doc-${message.id}-${props.children}`}
                className="inline-flex items-center justify-center w-5 h-5 text-xs font-semibold bg-primary/10 text-primary rounded-full no-underline mx-1 hover:bg-primary/20 transition-all border border-primary/20"
                title={props.href}
                onClick={(e) => {
                  e.preventDefault();
                  
                  // Expand sources to ensure the document is in DOM
                  setIsExpanded(true);
                  
                  // Trigger sidebar open if possible
                  const docIdx = Number(props.children);
                  if (onDocumentClick && message.documents && message.documents[docIdx]) {
                    onDocumentClick(message.documents[docIdx]);
                  }

                  // Wait a tick for React to render the expanded items
                  setTimeout(() => {
                    const el = document.getElementById(`doc-${message.id}-${props.children}`);
                    if (el) {
                      // Smooth scroll to element
                      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                      
                      // Remove highlight from any previously highlighted documents
                      document.querySelectorAll('.doc-highlight').forEach(node => {
                        node.classList.remove('doc-highlight', 'ring-2', 'ring-primary', 'ring-offset-2', 'ring-offset-background');
                      });
                      
                      // Add highlight animation
                      el.classList.add('doc-highlight', 'ring-2', 'ring-primary', 'ring-offset-2', 'ring-offset-background', 'transition-all');
                      
                      // Clear after 2s using a reference to avoid clearing a newly clicked one
                      if ((window as any)[`highlightTimeout-${message.id}`]) {
                        clearTimeout((window as any)[`highlightTimeout-${message.id}`]);
                      }
                      
                      (window as any)[`highlightTimeout-${message.id}`] = setTimeout(() => {
                        el.classList.remove('doc-highlight', 'ring-2', 'ring-primary', 'ring-offset-2', 'ring-offset-background');
                      }, 2000);
                    }
                  }, 50);
                }}
              >
                {props.children}
              </a>
            );
          }
          // Standard links
          return <a {...props} className="text-primary hover:underline font-medium" target="_blank" rel="noreferrer" />;
        }
      }}
    >
      {processedContent}
    </ReactMarkdown>
  );

  const renderDocuments = () => {
    if (!message.documents || message.documents.length === 0) return null;
    
    const maxVisible = 0;
    const hasMore = message.documents.length > maxVisible;
    const displayedDocs = isExpanded ? message.documents : message.documents.slice(0, maxVisible);
    
    return (
      <div className="mt-6 pt-4 border-t border-border/50">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold flex items-center gap-2 text-foreground/80">
            <FileText className="w-4 h-4" />
            Sources ({message.documents.length})
          </h4>
          {hasMore && (
            <button 
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs font-medium text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors px-2 py-1 rounded-md hover:bg-muted/50"
            >
              {isExpanded ? (
                <><ChevronUp className="w-3 h-3" /> Hide sources</>
              ) : (
                <><ChevronDown className="w-3 h-3" /> Show {message.documents.length} sources</>
              )}
            </button>
          )}
        </div>
        <div className="flex flex-col gap-2">
          {displayedDocs.map((doc, idx) => (
            <div 
              key={idx} 
              id={`doc-${message.id}-${idx}`} 
              onClick={() => onDocumentClick && onDocumentClick(doc)}
              className={cn(
                "bg-card w-full border border-border/60 transition-colors rounded-xl p-3 text-sm flex gap-3 shadow-sm scroll-mt-24",
                onDocumentClick ? "cursor-pointer hover:border-primary/50 hover:bg-accent/50 group" : "hover:border-border"
              )}
            >
              <div className="flex-shrink-0 mt-0.5">
               <span className={cn(
                 "bg-primary/10 text-primary text-xs font-semibold rounded-full w-5 h-5 flex items-center justify-center border border-primary/20",
                 onDocumentClick && "group-hover:bg-primary group-hover:text-primary-foreground group-hover:border-primary transition-all"
               )}>
                 {idx}
               </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-foreground font-medium text-sm mb-1 truncate" title={doc.source}>
                  {doc.source}
                </div>
                <div className="text-muted-foreground text-xs leading-relaxed line-clamp-2">
                  {doc.text}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (isUser) {
    return (
      <div className="flex w-full max-w-3xl mx-auto justify-end mb-4">
        <div className="bg-muted max-w-[85%] sm:max-w-[75%] rounded-3xl px-5 py-3 text-foreground leading-relaxed shadow-sm">
          <div className="prose prose-slate dark:prose-invert max-w-none text-base font-sans break-words prose-p:my-1 prose-pre:my-1">
            {renderMarkdown()}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full max-w-3xl mx-auto items-start mb-6">
      <div className="flex-1 space-y-2 overflow-hidden px-1 w-full relative">
        <div className="prose prose-slate dark:prose-invert max-w-none text-base font-sans leading-relaxed tracking-tight break-words">
          {renderMarkdown()}
        </div>
        {renderDocuments()}
      </div>
    </div>
  );
}
