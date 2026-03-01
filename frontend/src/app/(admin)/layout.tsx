import { AppLayout } from '@/components/layout/app-layout';
import * as React from 'react';

/**
 * Layout for admin/content pages like /documents.
 * Uses the shared AppLayout (sidebar + header) but renders children directly,
 * without the ChatInterface overlay used by the (chat) group.
 */
export default function AdminGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AppLayout>
      {children}
    </AppLayout>
  );
}
