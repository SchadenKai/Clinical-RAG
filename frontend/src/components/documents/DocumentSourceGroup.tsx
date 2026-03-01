import { CatalogDocument } from "@/hooks/use-catalog";
import { DocumentList } from "./DocumentList";
import { Building2, Globe } from "lucide-react";

interface DocumentSourceGroupProps {
  source: string;
  documents: CatalogDocument[];
}

export function DocumentSourceGroup({ source, documents }: DocumentSourceGroupProps) {
  const getSourceDetails = (src: string) => {
    switch (src?.toLowerCase()) {
      case "who":
        return {
          title: "World Health Organization",
          icon: <Globe className="w-5 h-5 text-blue-500" />,
          color: "border-blue-500/20 bg-blue-500/5",
        };
      case "cdc":
        return {
          title: "Centers for Disease Control and Prevention",
          icon: <Building2 className="w-5 h-5 text-emerald-500" />,
          color: "border-emerald-500/20 bg-emerald-500/5",
        };
      case "upload":
        return {
          title: "User Uploads",
          icon: <Building2 className="w-5 h-5 text-purple-500" />,
          color: "border-purple-500/20 bg-purple-500/5",
        };
      default:
        return {
          title: source || "Unknown Source",
          icon: <Building2 className="w-5 h-5 text-muted-foreground" />,
          color: "border-border bg-muted/20",
        };
    }
  };

  const details = getSourceDetails(source);

  return (
    <div className="space-y-4 mb-10">
      <div className="flex items-center gap-3 border-b pb-4">
        <div className={`p-2 rounded-lg ${details.color}`}>
          {details.icon}
        </div>
        <div>
          <h2 className="text-xl font-semibold tracking-tight">{details.title}</h2>
          <p className="text-sm text-muted-foreground">
            {documents.length} document{documents.length !== 1 ? "s" : ""}
          </p>
        </div>
      </div>
      
      <DocumentList documents={documents} />
    </div>
  );
}
