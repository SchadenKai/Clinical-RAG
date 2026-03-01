import { AppLayout } from '@/components/layout/app-layout';
import { ChatInterface } from '@/components/chat/chat-interface';

/**
 * Shared layout for / and /chat/[id].
 *
 * Keeping ChatInterface here (instead of inside each page) means it stays
 * *mounted* when the URL changes between the two routes — Next.js only
 * re-renders the deeper page segment, not this layout. That prevents the
 * "Loading conversation…" flash that was caused by the component unmounting
 * and remounting on every new-session navigation.
 *
 * The `children` slot is intentionally unused; both the root page and the
 * session page render `null` — all UI lives in ChatInterface which reads the
 * active session via `useParams()`.
 */
export default function ChatGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AppLayout>
      <ChatInterface />
      {/* children is kept in the tree so Next.js segment caching works correctly */}
      <div className="hidden">{children}</div>
    </AppLayout>
  );
}
