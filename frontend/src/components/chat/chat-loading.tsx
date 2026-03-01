interface ChatLoadingProps {
  message?: string;
}

export function ChatLoading({ message = 'Loading conversation...' }: ChatLoadingProps) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="flex items-center gap-2 text-muted-foreground animate-pulse">
        <div className="w-2 h-2 rounded-full bg-primary/40" />
        <div className="w-2 h-2 rounded-full bg-primary/40 animation-delay-200" />
        <div className="w-2 h-2 rounded-full bg-primary/40 animation-delay-400" />
        <span className="text-sm ml-2">{message}</span>
      </div>
    </div>
  );
}
