import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Upload, Folder as FolderIcon, Star, Trash2, Search, Plus, FileText, Loader2, ScanText, ChevronRight } from "lucide-react";
import { documentsApi, foldersApi } from "@/services/api";
import type { Document, Folder } from "@/types";

interface FolderNode extends Folder {
  children: FolderNode[];
}

function buildFolderTree(folders: Folder[]): FolderNode[] {
  const nodes = new Map<string, FolderNode>(folders.map((f) => [f.id, { ...f, children: [] }]));
  const roots: FolderNode[] = [];
  for (const f of folders) {
    const node = nodes.get(f.id)!;
    if (f.parent_folder_id && nodes.has(f.parent_folder_id)) {
      nodes.get(f.parent_folder_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  }
  return roots;
}

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [search, setSearch] = useState("");
  const [activeFolder, setActiveFolder] = useState<string | undefined>(undefined);
  const [uploadPct, setUploadPct] = useState<number | null>(null);

  const { data: documents } = useQuery({
    queryKey: ["documents", activeFolder, search],
    queryFn: async () => (await documentsApi.list({ folder_id: activeFolder, search: search || undefined })).data as Document[],
  });
  const { data: folders } = useQuery({
    queryKey: ["folders"],
    queryFn: async () => (await foldersApi.list()).data as Folder[],
  });
  const folderTree = useMemo(() => buildFolderTree(folders ?? []), [folders]);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentsApi.upload(file, activeFolder, setUploadPct),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setUploadPct(null);
    },
    onError: () => setUploadPct(null),
  });

  const favoriteMutation = useMutation({
    mutationFn: ({ id, is_favorite }: { id: string; is_favorite: boolean }) => documentsApi.update(id, { is_favorite }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  const createFolderMutation = useMutation({
    mutationFn: ({ name, parentId }: { name: string; parentId?: string }) => foldersApi.create(name, parentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["folders"] }),
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
    e.target.value = "";
  };

  const renderFolderNode = (node: FolderNode, depth = 0) => (
    <div key={node.id}>
      <button
        onClick={() => setActiveFolder(node.id)}
        style={{ paddingLeft: `${0.75 + depth * 0.9}rem` }}
        className={`flex w-full items-center gap-2 rounded-lg py-2 pr-3 text-sm ${
          activeFolder === node.id ? "bg-signal/15 text-signal" : "text-ink-700/70 hover:bg-ink-700/5 dark:text-paper-200/70 dark:hover:bg-white/5"
        }`}
      >
        {depth > 0 && <ChevronRight size={12} className="opacity-40" />}
        <FolderIcon size={15} /> <span className="truncate">{node.name}</span>
      </button>
      {node.children.map((child) => renderFolderNode(child, depth + 1))}
    </div>
  );

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink-900 dark:text-paper-50">Documents</h1>
          <p className="mt-1 text-ink-700/70 dark:text-paper-200/60">Upload files to chat with them.</p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex items-center gap-2 rounded-lg bg-signal px-4 py-2.5 text-sm font-medium text-white hover:opacity-90"
        >
          <Upload size={16} />
          Upload document
        </button>
        <input
          ref={fileInputRef}
          type="file"
          hidden
          onChange={handleFileSelect}
          accept=".pdf,.docx,.txt,.md,.csv,.xlsx,.pptx,.png,.jpg,.jpeg"
        />
      </div>

      {uploadPct !== null && (
        <div className="mt-4 rounded-lg border border-signal/30 bg-signal/5 px-4 py-2.5 text-sm text-signal">
          Uploading and processing (chunking, OCR if needed, embedding)... {uploadPct}%
        </div>
      )}

      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-[220px_1fr]">
        <aside className="space-y-1">
          <button
            onClick={() => setActiveFolder(undefined)}
            className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm ${
              !activeFolder ? "bg-signal/15 text-signal" : "text-ink-700/70 hover:bg-ink-700/5 dark:text-paper-200/70 dark:hover:bg-white/5"
            }`}
          >
            <FileText size={15} /> All documents
          </button>
          {folderTree.map((node) => renderFolderNode(node))}
          <button
            onClick={() => {
              const name = prompt("Folder name");
              if (name) createFolderMutation.mutate({ name, parentId: activeFolder });
            }}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-700/50 hover:bg-ink-700/5 dark:text-paper-200/40 dark:hover:bg-white/5"
          >
            <Plus size={15} /> New folder{activeFolder ? " (inside current)" : ""}
          </button>
        </aside>

        <div>
          <div className="relative mb-4">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-700/40 dark:text-paper-200/40" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search documents..."
              className="w-full rounded-lg border border-ink-700/20 bg-white/60 py-2.5 pl-9 pr-3 text-sm dark:border-ink-700/40 dark:bg-ink-900/50 dark:text-paper-50"
            />
          </div>

          <div className="overflow-hidden rounded-xl2 border border-ink-700/20 dark:border-ink-700/40">
            <table className="w-full text-sm">
              <thead className="bg-ink-700/5 text-left text-xs uppercase tracking-wide text-ink-700/50 dark:bg-white/5 dark:text-paper-200/50">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Chunks</th>
                  <th className="px-4 py-3 font-medium">Size</th>
                  <th className="px-4 py-3 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-700/10 dark:divide-ink-700/30">
                {documents?.map((doc) => (
                  <tr key={doc.id} className="text-ink-900 dark:text-paper-100">
                    <td className="flex items-center gap-2 px-4 py-3">
                      <FileText size={15} className="text-signal shrink-0" />
                      <span className="truncate">{doc.filename}</span>
                      {doc.is_scanned && (
                        <span title="Extracted via OCR" className="flex items-center gap-0.5 rounded bg-violet-400/10 px-1.5 py-0.5 text-[10px] text-violet-400">
                          <ScanText size={10} /> OCR
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {doc.status === "processing" || doc.status === "pending" ? (
                        <span className="flex items-center gap-1 text-amber">
                          <Loader2 size={12} className="animate-spin" /> Processing
                        </span>
                      ) : doc.status === "failed" ? (
                        <span className="text-red-400" title={doc.error_message ?? ""}>
                          Failed
                        </span>
                      ) : (
                        <span className="text-emerald-400">Ready</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-ink-700/60 dark:text-paper-200/50">{doc.embedding_count || "–"}</td>
                    <td className="px-4 py-3 text-ink-700/60 dark:text-paper-200/50">{(doc.file_size_bytes / 1024).toFixed(0)} KB</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => favoriteMutation.mutate({ id: doc.id, is_favorite: !doc.is_favorite })}
                          className={doc.is_favorite ? "text-amber" : "text-ink-700/30 hover:text-amber dark:text-paper-200/30"}
                        >
                          <Star size={15} fill={doc.is_favorite ? "currentColor" : "none"} />
                        </button>
                        <button
                          onClick={() => confirm(`Delete ${doc.filename}?`) && deleteMutation.mutate(doc.id)}
                          className="text-ink-700/30 hover:text-red-400 dark:text-paper-200/30"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!documents?.length && (
              <div className="px-4 py-10 text-center text-sm text-ink-700/50 dark:text-paper-200/40">No documents here yet.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
