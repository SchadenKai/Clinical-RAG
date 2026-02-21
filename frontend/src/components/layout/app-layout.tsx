import * as React from 'react';
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/layout/app-sidebar';

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <div className="flex w-full h-screen overflow-hidden bg-background">
        <AppSidebar />
        <main className="flex-1 flex flex-col relative w-full h-full min-w-0">
          <header className="absolute top-0 left-0 right-0 h-16 flex items-center px-4 md:px-6 z-10 bg-background/80 backdrop-blur-md border-b border-border/40">
            <SidebarTrigger className="md:hidden mr-4" />
            <div className="flex items-center gap-2">
              <h1 className="font-display font-medium text-lg tracking-tight">Clinical AI Dashboard</h1>
            </div>
          </header>
          
          <div className="pt-16 flex-1 w-full relative flex flex-col overflow-hidden">
            {children}
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
