'use client';

import * as React from 'react';
import { Plus, MessageSquare, Menu, Pencil, Trash2, Library } from 'lucide-react';

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuAction,
} from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { useSidebar } from '@/components/ui/sidebar';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useChatSessions, ChatSession } from '@/hooks/use-chat-sessions';

function ChatSessionItem({ session, chatId }: { session: ChatSession; chatId?: string }) {
  const [isEditing, setIsEditing] = React.useState(false);
  const [title, setTitle] = React.useState(session.title ?? 'New Chat');
  const { deleteSession, updateSession } = useChatSessions();
  const router = useRouter();

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    deleteSession.mutate(session.session_id, {
      onSuccess: () => {
        if (chatId === session.session_id) {
          router.push('/');
        }
      },
    });
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsEditing(true);
  };

  const saveEdit = () => {
    setIsEditing(false);
    if (title.trim() !== '' && title !== (session.title ?? 'New Chat')) {
      updateSession.mutate({ sessionId: session.session_id, title: title.trim() });
    } else {
      setTitle(session.title ?? 'New Chat');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      saveEdit();
    } else if (e.key === 'Escape') {
      setTitle(session.title ?? 'New Chat');
      setIsEditing(false);
    }
  };

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={!!chatId && session.session_id === chatId}>
        {isEditing ? (
          <div className="flex items-center w-full">
             <MessageSquare className="mr-2 h-4 w-4 shrink-0 opacity-70" />
             <input
                type="text"
                className="flex-1 bg-transparent outline-none ring-0 w-full text-sm"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onBlur={saveEdit}
                onKeyDown={handleKeyDown}
                autoFocus
             />
          </div>
        ) : (
          <Link
             href={`/chat/${session.session_id}`}
             className="truncate transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
             <MessageSquare className="mr-2 h-4 w-4 shrink-0 opacity-70" />
             <span className="truncate">{session.title ?? 'New Chat'}</span>
          </Link>
        )}
      </SidebarMenuButton>
      {!isEditing && (
        <>
          <SidebarMenuAction showOnHover className="right-7" onClick={handleEdit} title="Rename chat">
            <Pencil className="h-4 w-4" />
          </SidebarMenuAction>
          <SidebarMenuAction showOnHover onClick={handleDelete} title="Delete chat">
            <Trash2 className="h-4 w-4" />
          </SidebarMenuAction>
        </>
      )}
    </SidebarMenuItem>
  );
}

export function AppSidebar() {
  const { toggleSidebar } = useSidebar();
  const router = useRouter();
  const params = useParams();
  const chatId = typeof params?.id === 'string' ? params.id : undefined;
  const { sessions, isLoading } = useChatSessions();

  const handleNewChat = () => {
    router.push('/');
  };

  return (
    <Sidebar className="border-r border-sidebar-border/50">
      <SidebarHeader className="p-4 flex flex-row items-center justify-between">
        <h2 className="text-lg font-display font-semibold text-sidebar-foreground">
          Clinical AI
        </h2>
        <Button variant="ghost" size="icon" onClick={() => toggleSidebar()} className="md:hidden">
          <Menu className="h-4 w-4" />
        </Button>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <div className="px-4 py-2 space-y-2">
            <Button
              className="w-full justify-start gap-2 shadow-sm font-medium"
              variant="default"
              onClick={handleNewChat}
            >
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
            <Button
              className="w-full justify-start gap-2 shadow-sm font-medium"
              variant="secondary"
              onClick={() => router.push('/documents')}
            >
              <Library className="h-4 w-4 text-muted-foreground" />
              Knowledge Base
            </Button>
          </div>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold tracking-wider text-sidebar-foreground/60 uppercase">
            Recent Chats
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {isLoading ? (
                // Skeleton placeholders while sessions are loading
                Array.from({ length: 3 }).map((_, i) => (
                  <SidebarMenuItem key={`skeleton-${i}`}>
                    <div className="h-8 rounded-md bg-sidebar-accent/40 animate-pulse mx-2 my-1" />
                  </SidebarMenuItem>
                ))
              ) : sessions.length === 0 ? (
                <p className="px-4 py-3 text-xs text-sidebar-foreground/50 italic">
                  No conversations yet.
                </p>
              ) : (
                sessions.map((session) => (
                  <ChatSessionItem key={session.session_id} session={session} chatId={chatId} />
                ))
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
