"use client";

import { useEffect, useMemo, useState } from "react";
import { useCatalog, CatalogDocument } from "@/hooks/use-catalog";
import { DocumentSourceGroup } from "@/components/documents/DocumentSourceGroup";
import { RefreshCcw, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function DocumentsPage() {
  const { documents, loading, error, fetchCatalog } = useCatalog();
  const [searchQuery, setSearchQuery] = useState("");

  const loadDocs = () => {
    fetchCatalog(undefined, undefined, "ALL", 1);
  };

  useEffect(() => {
    loadDocs();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Group documents by source
  const groupedDocuments = useMemo(() => {
    const filtered = searchQuery
      ? documents.filter((doc) =>
          doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : documents;

    const groups: Record<string, CatalogDocument[]> = {};
    filtered.forEach((doc) => {
      const source = doc.source || "Other";
      if (!groups[source]) {
        groups[source] = [];
      }
      groups[source].push(doc);
    });
    return groups;
  }, [documents, searchQuery]);

  return (
    <div className="flex-1 space-y-6 flex flex-col h-full overflow-hidden">
      <div className="flex-none p-6 pb-2 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Document Management</h1>
            <p className="text-muted-foreground mt-1">
              View and manage documents stored in the knowledge base.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
            onClick={loadDocs}
            disabled={loading}
          >
            <RefreshCcw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        <div className="mt-6 flex items-center gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search documents by name..."
              className="pl-9"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6 pt-4">
        {error && (
          <div className="p-4 mb-6 text-sm text-red-500 bg-red-500/10 rounded-lg border border-red-500/20">
            Error loading documents: {error}
          </div>
        )}

        {Object.keys(groupedDocuments).length === 0 && !loading && !error && (
          <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
            <p>No documents found matching your criteria.</p>
          </div>
        )}

        {Object.entries(groupedDocuments).map(([source, docs]) => (
          <DocumentSourceGroup key={source} source={source} documents={docs} />
        ))}
      </div>
    </div>
  );
}
