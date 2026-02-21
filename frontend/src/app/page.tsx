import { AppLayout } from '@/components/layout/app-layout';
import { ChatInterface } from '@/components/chat/chat-interface';

export default function Page() {
  return (
    <AppLayout>
      <ChatInterface />
    </AppLayout>
  );
}
