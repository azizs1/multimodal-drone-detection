"use client";

import { useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import {
  type IncidentDetailPanelData,
  type IncidentTableRow,
  mapIncidentResponseToDetail,
  mapIncidentResponseToRow,
} from "@/lib/incidents.mjs";
import { getIncidents, type IncidentResponse } from "@/lib/api/incidents";
import { IncidentDetailPanel } from "@/components/incidents/incident-detail-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
} from "@/components/ui/pagination";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const ALL_DECISIONS = ["all", "drone", "none"] as const;
const ALL_ALERT_LEVELS = ["all", "low", "medium", "high"] as const;
const PAGE_SIZE = 10;
const DEFAULT_LIMIT = 1000;
const RANGE_LIMIT = 10000;

function formatDisplayTimestamp(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return format(date, "yyyy-MM-dd HH:mm:ss");
}

function formatConfidencePercentage(value: number): string {
  const normalized = value <= 1 ? value * 100 : value;
  return `${Math.round(normalized)}%`;
}

function getDecisionBadgeClasses(decision: IncidentTableRow["decision"]): string {
  return decision === "drone"
    ? "border-transparent bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300"
    : "border-transparent bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200";
}

function getAlertLevelBadgeClasses(alertLevel: IncidentTableRow["alertLevel"]): string {
  if (alertLevel === "high") {
    return "border-transparent bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300";
  }

  if (alertLevel === "medium") {
    return "border-transparent bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300";
  }

  return "border-transparent bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300";
}

function toDateTimeInputValue(value: Date | undefined): string {
  if (!value) {
    return "";
  }

  const offset = value.getTimezoneOffset();
  const localDate = new Date(value.getTime() - offset * 60_000);
  return localDate.toISOString().slice(0, 16);
}

function parseDateTimeInputValue(value: string): Date | undefined {
  if (!value) {
    return undefined;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? undefined : parsed;
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);
  const [decision, setDecision] = useState<(typeof ALL_DECISIONS)[number]>("all");
  const [alertLevel, setAlertLevel] = useState<(typeof ALL_ALERT_LEVELS)[number]>("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedIncident, setSelectedIncident] = useState<IncidentDetailPanelData | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const hasActiveFilters = Boolean(startDate || endDate || decision !== "all" || alertLevel !== "all");
  const hasTimeRange = Boolean(startDate || endDate);

  useEffect(() => {
    let isMounted = true;

    async function loadIncidents() {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const response = await getIncidents({
          limit: hasTimeRange ? RANGE_LIMIT : DEFAULT_LIMIT,
          decision: decision !== "all" ? decision : undefined,
          fromTs: startDate?.toISOString(),
          toTs: endDate?.toISOString(),
        });

        if (!isMounted) {
          return;
        }

        setIncidents(response);
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setErrorMessage(error instanceof Error ? error.message : "Failed to load incidents.");
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadIncidents();

    return () => {
      isMounted = false;
    };
  }, [decision, endDate, hasTimeRange, startDate]);

  const tableRows = useMemo(
    () => incidents.map((incident) => mapIncidentResponseToRow(incident)),
    [incidents],
  );

  const filteredRows = useMemo(() => {
    return tableRows.filter((row) => {
      const matchesAlertLevel = alertLevel === "all" || row.alertLevel === alertLevel;
      return matchesAlertLevel;
    });
  }, [alertLevel, tableRows]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE));
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const pageStart = (safeCurrentPage - 1) * PAGE_SIZE;
  const pagedRows = filteredRows.slice(pageStart, pageStart + PAGE_SIZE);
  const pageWindowStart = Math.max(1, Math.min(safeCurrentPage - 1, totalPages - 2));
  const visiblePages = Array.from(
    { length: Math.min(3, totalPages) },
    (_, index) => pageWindowStart + index,
  );

  const openIncidentDetail = (row: IncidentTableRow) => {
    const incident = incidents.find((entry) => entry.incident_id === row.incidentId);

    if (!incident) {
      return;
    }

    setSelectedIncident(mapIncidentResponseToDetail(incident));
    setIsDetailOpen(true);
  };

  return (
    <DashboardShell>
      <section className="space-y-4">
        <IncidentDetailPanel
          incident={selectedIncident}
          open={isDetailOpen}
          onOpenChange={(open) => {
            setIsDetailOpen(open);
            if (!open) {
              setSelectedIncident(null);
            }
          }}
        />

        <div className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Start
              <Input
                type="datetime-local"
                value={toDateTimeInputValue(startDate)}
                onChange={(event) => {
                  setStartDate(parseDateTimeInputValue(event.target.value));
                  setCurrentPage(1);
                }}
                className="mt-1 border-slate-300 bg-slate-50 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            </label>

            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              End
              <Input
                type="datetime-local"
                value={toDateTimeInputValue(endDate)}
                onChange={(event) => {
                  setEndDate(parseDateTimeInputValue(event.target.value));
                  setCurrentPage(1);
                }}
                className="mt-1 border-slate-300 bg-slate-50 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            </label>

            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Decision
              <Select
                value={decision}
                onValueChange={(value) => {
                  setDecision(value as (typeof ALL_DECISIONS)[number]);
                  setCurrentPage(1);
                }}
              >
                <SelectTrigger className="mt-1 w-full border-slate-300 bg-slate-50 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100">
                  <SelectValue placeholder="All decisions" />
                </SelectTrigger>
                <SelectContent>
                  {ALL_DECISIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </label>

            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Alert Level
              <Select
                value={alertLevel}
                onValueChange={(value) => {
                  setAlertLevel(value as (typeof ALL_ALERT_LEVELS)[number]);
                  setCurrentPage(1);
                }}
              >
                <SelectTrigger className="mt-1 w-full border-slate-300 bg-slate-50 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100">
                  <SelectValue placeholder="All alert levels" />
                </SelectTrigger>
                <SelectContent>
                  {ALL_ALERT_LEVELS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
                  setDecision("all");
                  setAlertLevel("all");
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
          {errorMessage ? (
            <div className="mb-4 rounded-sm border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800 dark:border-rose-700/60 dark:bg-rose-900/20 dark:text-rose-200">
              Failed to load incidents: {errorMessage}
            </div>
          ) : null}

          <Table className="min-w-[880px] text-left text-sm text-slate-700 dark:text-slate-200">
            <TableHeader className="text-slate-500 dark:text-slate-400">
              <TableRow className="border-b border-slate-300 hover:bg-transparent dark:border-slate-700">
                <TableHead className="px-2 py-3 font-semibold">Detected At</TableHead>
                <TableHead className="px-2 py-3 font-semibold">Decision</TableHead>
                <TableHead className="px-2 py-3 font-semibold">Alert Level</TableHead>
                <TableHead className="px-2 py-3 font-semibold">Fused Confidence</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pagedRows.map((row) => (
                <TableRow
                  key={`${row.incidentId}-${row.detectedAt}`}
                  className={`cursor-pointer border-b border-slate-200 transition-colors dark:border-slate-800 ${
                    selectedIncident?.id === row.incidentId
                      ? "bg-slate-100 hover:bg-slate-200/80 dark:bg-slate-800/80 dark:hover:bg-slate-800"
                      : "hover:bg-slate-100/80 dark:hover:bg-slate-800/60"
                  }`}
                  tabIndex={0}
                  role="button"
                  onClick={() => openIncidentDetail(row)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      openIncidentDetail(row);
                    }
                  }}
                >
                  <TableCell className="px-2 py-3">
                    {formatDisplayTimestamp(row.detectedAt)}
                  </TableCell>
                  <TableCell className="px-2 py-3">
                    <Badge className={`px-3 py-1 text-sm font-semibold uppercase ${getDecisionBadgeClasses(row.decision)}`}>
                      {row.decision}
                    </Badge>
                  </TableCell>
                  <TableCell className="px-2 py-3">
                    <Badge
                      className={`px-3 py-1 text-sm font-semibold uppercase ${getAlertLevelBadgeClasses(row.alertLevel)}`}
                    >
                      {row.alertLevel}
                    </Badge>
                  </TableCell>
                  <TableCell className="px-2 py-3">{formatConfidencePercentage(row.fusedConfidence)}</TableCell>
                </TableRow>
              ))}
              {!isLoading && pagedRows.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell className="px-2 py-6 text-center text-slate-500 dark:text-slate-400" colSpan={4}>
                    No incidents found for current filters.
                  </TableCell>
                </TableRow>
              ) : null}
              {isLoading ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell className="px-2 py-6 text-center text-slate-500 dark:text-slate-400" colSpan={4}>
                    Loading incidents...
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
                    <Button
                      type="button"
                      onClick={() => setCurrentPage(page)}
                      aria-current={safeCurrentPage === page ? "page" : undefined}
                      className={`size-9 border border-slate-300 px-0 text-sm font-medium dark:border-slate-700 ${
                        safeCurrentPage === page
                          ? "bg-slate-200 text-slate-800 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-700"
                          : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                      }`}
                    >
                      {page}
                    </Button>
                  </PaginationItem>
                ))}
                <PaginationItem>
                  <Button
                    type="button"
                    onClick={() => {
                      if (safeCurrentPage > 1) {
                        setCurrentPage((prev) => Math.max(1, prev - 1));
                      }
                    }}
                    disabled={safeCurrentPage === 1}
                    aria-disabled={safeCurrentPage === 1}
                    className="h-9 w-10 border border-slate-300 bg-slate-100 px-0 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                  >
                    <span className="sr-only">Previous page</span>
                    &lt;
                  </Button>
                </PaginationItem>
                <PaginationItem>
                  <Button
                    type="button"
                    onClick={() => {
                      if (safeCurrentPage < totalPages) {
                        setCurrentPage((prev) => Math.min(totalPages, prev + 1));
                      }
                    }}
                    disabled={safeCurrentPage === totalPages}
                    aria-disabled={safeCurrentPage === totalPages}
                    className="h-9 w-10 border border-slate-300 bg-slate-100 px-0 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                  >
                    <span className="sr-only">Next page</span>
                    &gt;
                  </Button>
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        </div>
      </section>
    </DashboardShell>
  );
}
