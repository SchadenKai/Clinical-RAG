import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Circle, Clock, AlertCircle, Loader2 } from "lucide-react";

interface DocumentStatusBadgeProps {
  status: string;
}

export function DocumentStatusBadge({ status }: DocumentStatusBadgeProps) {
  const normalizedStatus = status?.toUpperCase() || "PENDING";

  switch (normalizedStatus) {
    case "INDEXED":
      return (
        <Badge variant="default" className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border-emerald-500/20 shadow-none font-normal">
          <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
          Indexed
        </Badge>
      );
    case "INDEXING":
      return (
        <Badge variant="secondary" className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 border-blue-500/20 shadow-none font-normal">
          <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
          Indexing
        </Badge>
      );
    case "FAILED":
      return (
        <Badge variant="destructive" className="bg-red-500/10 text-red-500 hover:bg-red-500/20 border-red-500/20 shadow-none font-normal">
          <AlertCircle className="w-3.5 h-3.5 mr-1.5" />
          Failed
        </Badge>
      );
    case "PENDING":
    default:
      return (
        <Badge variant="outline" className="text-muted-foreground shadow-none font-normal border-border/50 bg-muted/20">
          <Clock className="w-3.5 h-3.5 mr-1.5" />
          Pending
        </Badge>
      );
  }
}
