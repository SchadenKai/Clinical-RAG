'use client';

import * as React from 'react';
import { Plus, MessageSquare, Menu } from 'lucide-react';

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
  SidebarTrigger,
} from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { useSidebar } from '@/components/ui/sidebar';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import db from '@/lib/dummy-db.json';

export function AppSidebar() {
  const { toggleSidebar } = useSidebar();
  const params = useParams();
  const chatId = typeof params?.id === 'string' ? params.id : undefined;
  const chats = db.chatHistory;

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
          <div className="px-4 py-2">
            <Button asChild className="w-full justify-start gap-2 shadow-sm font-medium" variant="default">
              <Link href="/">
                <Plus className="h-4 w-4" />
                New Chat
              </Link>
            </Button>
          </div>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold tracking-wider text-sidebar-foreground/60 uppercase">
            Recent Chats
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {chats.map((chat) => (
                <SidebarMenuItem key={chat.id}>
                  <SidebarMenuButton asChild isActive={chat.id === chatId}>
                    <Link href={`/chat/${chat.id}`} className="truncate transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground">
                      <MessageSquare className="mr-2 h-4 w-4 shrink-0 opacity-70" />
                      <span className="truncate">{chat.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
