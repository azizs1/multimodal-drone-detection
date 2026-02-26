"use client";

import { useMemo, useState } from "react";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Input } from "@/components/ui/input";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type IncidentLogRow = {
  id: string;
  timestamp: string;
  confidence: number;
  distanceFt: number;
  model: string;
  status: "Confirmed" | "Pending" | "False Positive";
};

const ALL_STATUSES = ["All", "Confirmed", "Pending", "False Positive"] as const;
const PAGE_SIZE = 10;

function toDateKey(date: Date): string {
  return format(date, "yyyy-MM-dd");
}

function generateMockIncidents(count: number): IncidentLogRow[] {
  const statuses: IncidentLogRow["status"][] = ["Confirmed", "Pending", "False Positive"];
  const rows: IncidentLogRow[] = [];

  for (let i = 1; i <= count; i += 1) {
    const day = 18 + Math.floor((i - 1) / 12);
    const hour = 10 + (i % 10);
    const minute = (7 + i * 3) % 60;
    const second = (11 + i * 5) % 60;
    const status = statuses[i % statuses.length];

    rows.push({
      id: `#${String(i).padStart(3, "0")}`,
      timestamp: `2026-02-${String(day).padStart(2, "0")}T${String(hour).padStart(2, "0")}:${String(
        minute,
      ).padStart(2, "0")}:${String(second).padStart(2, "0")}`,
      confidence: 70 + (i % 26),
      distanceFt: 8 + (i % 18),
      model: i % 5 === 0 ? "HolyStone-v2" : "HolyStone",
      status,
    });
  }

  return rows;
}

const INCIDENT_LOG_ROWS: IncidentLogRow[] = generateMockIncidents(48);

const STATUS_BADGE_CLASSES: Record<IncidentLogRow["status"], string> = {
  Confirmed:
    "border-transparent bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  Pending: "border-transparent bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  "False Positive": "border-transparent bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300",
};

export default function IncidentsPage() {
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);
  const [status, setStatus] = useState<(typeof ALL_STATUSES)[number]>("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const hasActiveFilters = Boolean(startDate || endDate || searchTerm.trim() || status !== "All");

  const filteredRows = useMemo(() => {
    const startKey = startDate ? toDateKey(startDate) : "";
    const endKey = endDate ? toDateKey(endDate) : "";

    return INCIDENT_LOG_ROWS.filter((row) => {
      const rowDate = row.timestamp.slice(0, 10);
      const matchesStart = !startKey || rowDate >= startKey;
      const matchesEnd = !endKey || rowDate <= endKey;
      const matchesStatus = status === "All" || row.status === status;
      const query = searchTerm.trim().toLowerCase();
      const matchesSearch =
        query.length === 0 || row.id.toLowerCase().includes(query) || row.model.toLowerCase().includes(query);

      return matchesStart && matchesEnd && matchesStatus && matchesSearch;
    });
  }, [endDate, searchTerm, startDate, status]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE));
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const pageStart = (safeCurrentPage - 1) * PAGE_SIZE;
  const pagedRows = filteredRows.slice(pageStart, pageStart + PAGE_SIZE);
  const pageWindowStart = Math.max(1, Math.min(safeCurrentPage - 1, totalPages - 2));
  const visiblePages = Array.from(
    { length: Math.min(3, totalPages) },
    (_, index) => pageWindowStart + index,
  );

  return (
    <DashboardShell>
      <section className="space-y-4">
        <div className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
            <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Start Date
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className="mt-1 w-full justify-between border-slate-300 bg-slate-50 text-sm font-normal text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
                  >
                    {startDate ? toDateKey(startDate) : "Select date"}
                    <CalendarIcon className="size-4 text-slate-500 dark:text-slate-400" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto border-slate-300 p-0 dark:border-slate-700" align="start">
                  <Calendar
                    mode="single"
                    selected={startDate}
                    onSelect={(date) => {
                      setStartDate(date);
                      setCurrentPage(1);
                    }}
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
              End Date
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className="mt-1 w-full justify-between border-slate-300 bg-slate-50 text-sm font-normal text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
                  >
                    {endDate ? toDateKey(endDate) : "Select date"}
                    <CalendarIcon className="size-4 text-slate-500 dark:text-slate-400" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto border-slate-300 p-0 dark:border-slate-700" align="start">
                  <Calendar
                    mode="single"
                    selected={endDate}
                    onSelect={(date) => {
                      setEndDate(date);
                      setCurrentPage(1);
                    }}
                  />
                </PopoverContent>
              </Popover>
            </div>

            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Status
              <Select
                value={status}
                onValueChange={(value) => {
                  setStatus(value as (typeof ALL_STATUSES)[number]);
                  setCurrentPage(1);
                }}
              >
                <SelectTrigger className="mt-1 w-full border-slate-300 bg-slate-50 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100">
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  {ALL_STATUSES.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </label>

            <label className="text-sm font-medium text-slate-700 xl:col-span-2 dark:text-slate-300">
              Search
              <Input
                type="text"
                value={searchTerm}
                onChange={(event) => {
                  setSearchTerm(event.target.value);
                  setCurrentPage(1);
                }}
                placeholder="Search ID or model..."
                className="mt-1 border-slate-300 bg-slate-50 text-sm text-slate-700 placeholder:text-slate-400 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
              />
            </label>

            <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Reset
              <Button
                type="button"
                variant="outline"
                disabled={!hasActiveFilters}
                onClick={() => {
                  setStartDate(undefined);
                  setEndDate(undefined);
                  setStatus("All");
                  setSearchTerm("");
                  setCurrentPage(1);
                }}
                className="mt-1 w-full border-slate-300 bg-slate-100 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
              >
                Reset Filters
              </Button>
            </div>
          </div>
        </div>

        <div className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <Table className="min-w-[880px] text-left text-sm text-slate-700 dark:text-slate-200">
            <TableHeader className="text-slate-500 dark:text-slate-400">
              <TableRow className="border-b border-slate-300 hover:bg-transparent dark:border-slate-700">
                <TableHead className="px-2 py-3 font-semibold">ID</TableHead>
                <TableHead className="px-2 py-3 font-semibold">Timestamp</TableHead>
                <TableHead className="px-2 py-3 font-semibold">Confidence</TableHead>
                <TableHead className="px-2 py-3 font-semibold">Distance</TableHead>
                <TableHead className="px-2 py-3 font-semibold">Model</TableHead>
                <TableHead className="px-2 py-3 font-semibold">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pagedRows.map((row) => (
                <TableRow key={`${row.id}-${row.timestamp}`} className="border-b border-slate-200 dark:border-slate-800">
                  <TableCell className="px-2 py-3">{row.id}</TableCell>
                  <TableCell className="px-2 py-3">
                    {format(new Date(row.timestamp), "yyyy-MM-dd HH:mm:ss")}
                  </TableCell>
                  <TableCell className="px-2 py-3">{row.confidence}%</TableCell>
                  <TableCell className="px-2 py-3">{row.distanceFt}ft</TableCell>
                  <TableCell className="px-2 py-3">{row.model}</TableCell>
                  <TableCell className="px-2 py-3">
                    <Badge className={`px-3 py-1 text-sm font-semibold ${STATUS_BADGE_CLASSES[row.status]}`}>
                      {row.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
              {pagedRows.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell className="px-2 py-6 text-center text-slate-500 dark:text-slate-400" colSpan={6}>
                    No incidents found for current filters.
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>

          <div className="mt-4 flex items-center justify-between text-sm text-slate-600 dark:text-slate-300">
            <p>
              Showing {pagedRows.length === 0 ? 0 : pageStart + 1}-{pageStart + pagedRows.length} of{" "}
              {filteredRows.length}
            </p>
            <Pagination className="mx-0 w-auto justify-end">
              <PaginationContent>
                {visiblePages.map((page) => (
                  <PaginationItem key={page}>
                    <PaginationLink
                      href="#"
                      isActive={safeCurrentPage === page}
                      onClick={(event) => {
                        event.preventDefault();
                        setCurrentPage(page);
                      }}
                      className={`size-9 border border-slate-300 px-0 text-sm font-medium dark:border-slate-700 ${
                        safeCurrentPage === page
                          ? "bg-slate-200 text-slate-800 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-700"
                          : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                      }`}
                    >
                      {page}
                    </PaginationLink>
                  </PaginationItem>
                ))}
                <PaginationItem>
                  <PaginationPrevious
                    href="#"
                    onClick={(event) => {
                      event.preventDefault();
                      if (safeCurrentPage > 1) {
                        setCurrentPage((prev) => Math.max(1, prev - 1));
                      }
                    }}
                    aria-disabled={safeCurrentPage === 1}
                    className={`h-9 border border-slate-300 bg-slate-100 text-slate-700 hover:bg-slate-200 [&>span]:hidden dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 ${
                      safeCurrentPage === 1 ? "pointer-events-none opacity-50" : ""
                    }`}
                  />
                </PaginationItem>
                <PaginationItem>
                  <PaginationNext
                    href="#"
                    onClick={(event) => {
                      event.preventDefault();
                      if (safeCurrentPage < totalPages) {
                        setCurrentPage((prev) => Math.min(totalPages, prev + 1));
                      }
                    }}
                    aria-disabled={safeCurrentPage === totalPages}
                    className={`h-9 border border-slate-300 bg-slate-100 text-slate-700 hover:bg-slate-200 [&>span]:hidden dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 ${
                      safeCurrentPage === totalPages ? "pointer-events-none opacity-50" : ""
                    }`}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        </div>
      </section>
    </DashboardShell>
  );
}
