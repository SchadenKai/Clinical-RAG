import { CatalogDocument } from "@/hooks/use-catalog";
import { DocumentStatusBadge } from "./DocumentStatusBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { FileText, ExternalLink } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface DocumentListProps {
  documents: CatalogDocument[];
}

export function DocumentList({ documents }: DocumentListProps) {
  if (!documents || documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center bg-card rounded-lg border border-border/50 text-muted-foreground">
        <FileText className="w-10 h-10 mb-3 opacity-20" />
        <p>No documents found</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-border/50 bg-card overflow-hidden">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow>
            <TableHead className="w-[50%]">Filename</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Indexed At</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.map((doc) => (
            <TableRow key={doc.id} className="hover:bg-muted/30 transition-colors">
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary/60" />
                  <span className="truncate">{doc.filename}</span>
                </div>
              </TableCell>
              <TableCell>
                <DocumentStatusBadge status={doc.status} />
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {doc.indexed_at
                  ? formatDistanceToNow(new Date(doc.indexed_at), { addSuffix: true })
                  : "-"}
              </TableCell>
              <TableCell className="text-right">
                {doc.url && (
                  <a
                    href={doc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-8 w-8 text-muted-foreground"
                    title="View Original"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
