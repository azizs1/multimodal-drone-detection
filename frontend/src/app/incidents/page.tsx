"use client";

import { useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import {
  type IncidentDetailPanelData,
  type IncidentTableRow,
  getIncidentDisplayId,
  mapIncidentResponseToDetail,
  mapIncidentResponseToRow,
} from "@/lib/incidents.mjs";
import { getIncidents, getRawIncidents, type IncidentResponse } from "@/lib/api/incidents";
import { IncidentDetailPanel } from "@/components/incidents/incident-detail-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
} from "@/components/ui/pagination";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const ALL_DECISIONS = ["all", "drone", "none"] as const;
const ALL_ALERT_LEVELS = ["all", "low", "medium", "high"] as const;
const PAGE_SIZE = 10;
const DEFAULT_LIMIT = 1000;
const RANGE_LIMIT = 1000;
const HOUR_OPTIONS = Array.from({ length: 24 }, (_, index) => String(index).padStart(2, "0"));
const MINUTE_OPTIONS = Array.from({ length: 60 }, (_, index) => String(index).padStart(2, "0"));

type DateTimePickerProps = {
  label: string;
  value: Date | undefined;
  onChange: (value: Date | undefined) => void;
  onCommit: () => void;
};

type QuickRangeKey = "lastHour" | "today" | "last7Days";
type IncidentView = "aggregated" | "raw";

function formatDisplayTimestamp(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return format(date, "yyyy-MM-dd HH:mm:ss");
}

function formatApiDateTime(value: Date | undefined): string | undefined {
  if (!value) {
    return undefined;
  }

  return value.toISOString().replace(/\.\d{3}Z$/, "Z");
}

function formatConfidencePercentage(value: number): string {
  const normalized = value <= 1 ? value * 100 : value;
  return `${Math.round(normalized)}%`;
}

function formatCount(value: number | null): string {
  return typeof value === "number" ? String(value) : "--";
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

function getIncidentViewButtonClasses(view: IncidentView, activeView: IncidentView): string {
  return view === activeView
    ? "border-slate-900 bg-slate-900 text-slate-50 hover:bg-slate-900 hover:text-slate-50 dark:border-slate-100 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-100 dark:hover:text-slate-900"
    : "border-slate-300 bg-slate-50 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700";
}

function formatPickerLabel(value: Date | undefined): string {
  if (!value) {
    return "Select date and time";
  }

  return format(value, "yyyy/MM/dd HH:mm");
}

function updateDatePart(current: Date | undefined, selectedDate: Date | undefined): Date | undefined {
  if (!selectedDate) {
    return undefined;
  }

  const next = new Date(selectedDate);
  next.setSeconds(0, 0);

  if (current) {
    next.setHours(current.getHours(), current.getMinutes(), 0, 0);
    return next;
  }

  next.setHours(0, 0, 0, 0);
  return next;
}

function updateTimePart(current: Date | undefined, part: "hour" | "minute", value: string): Date | undefined {
  if (!current) {
    return current;
  }

  const next = new Date(current);

  if (part === "hour") {
    next.setHours(Number(value));
  } else {
    next.setMinutes(Number(value));
  }

  next.setSeconds(0, 0);
  return next;
}

function getRangeValidationMessage(start: Date | undefined, end: Date | undefined): string | null {
  if (start && end && start > end) {
    return "Start time must be earlier than end time.";
  }

  return null;
}

function getQuickRange(range: QuickRangeKey): { start: Date; end: Date } {
  const now = new Date();

  if (range === "lastHour") {
    return {
      start: new Date(now.getTime() - 60 * 60 * 1000),
      end: now,
    };
  }

  if (range === "today") {
    const start = new Date(now);
    start.setHours(0, 0, 0, 0);
    return {
      start,
      end: now,
    };
  }

  return {
    start: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
    end: now,
  };
}

function DateTimePicker({ label, value, onChange, onCommit }: DateTimePickerProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
      {label}
      <Popover
        open={open}
        onOpenChange={(nextOpen) => {
          setOpen(nextOpen);
          if (!nextOpen) {
            onCommit();
          }
        }}
      >
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            className="mt-1 h-auto w-full items-center justify-between border-slate-300 bg-slate-50 px-3 py-2 text-left font-normal text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            <span className="flex min-w-0 flex-col">
              <span className="truncate text-sm">{formatPickerLabel(value)}</span>
            </span>
            <CalendarIcon className="size-4 shrink-0 text-slate-500 dark:text-slate-400" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-fit border-slate-300 p-0 dark:border-slate-700" align="start">
          <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{label}</p>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                onChange(undefined);
              }}
              className="h-8 px-2 text-slate-600 hover:bg-transparent hover:text-slate-900 dark:text-slate-300 dark:hover:bg-transparent dark:hover:text-slate-100"
            >
              Clear
            </Button>
          </div>
          <div className="w-fit">
            <Calendar
              mode="single"
              selected={value}
              onSelect={(selectedDate) => onChange(updateDatePart(value, selectedDate))}
            />
          </div>
          <div className="border-t border-slate-200 px-4 py-3 dark:border-slate-800">
            <div className="flex items-end gap-3">
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Hour
                <Select
                  value={value ? String(value.getHours()).padStart(2, "0") : undefined}
                  onValueChange={(selectedHour) => onChange(updateTimePart(value, "hour", selectedHour))}
                  disabled={!value}
                >
                  <SelectTrigger className="mt-1 w-[96px] border-slate-300 bg-slate-50 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
                    <SelectValue placeholder="HH" />
                  </SelectTrigger>
                  <SelectContent>
                    {HOUR_OPTIONS.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </label>

              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Minute
                <Select
                  value={value ? String(value.getMinutes()).padStart(2, "0") : undefined}
                  onValueChange={(selectedMinute) => onChange(updateTimePart(value, "minute", selectedMinute))}
                  disabled={!value}
                >
                  <SelectTrigger className="mt-1 w-[96px] border-slate-300 bg-slate-50 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
                    <SelectValue placeholder="MM" />
                  </SelectTrigger>
                  <SelectContent>
                    {MINUTE_OPTIONS.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </label>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [activeView, setActiveView] = useState<IncidentView>("aggregated");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [draftStartDate, setDraftStartDate] = useState<Date | undefined>(undefined);
  const [draftEndDate, setDraftEndDate] = useState<Date | undefined>(undefined);
  const [draftDecision, setDraftDecision] = useState<(typeof ALL_DECISIONS)[number]>("all");
  const [draftAlertLevel, setDraftAlertLevel] = useState<(typeof ALL_ALERT_LEVELS)[number]>("all");
  const [appliedStartDate, setAppliedStartDate] = useState<Date | undefined>(undefined);
  const [appliedEndDate, setAppliedEndDate] = useState<Date | undefined>(undefined);
  const [appliedDecision, setAppliedDecision] = useState<(typeof ALL_DECISIONS)[number]>("all");
  const [appliedAlertLevel, setAppliedAlertLevel] = useState<(typeof ALL_ALERT_LEVELS)[number]>("all");
  const [activeQuickRange, setActiveQuickRange] = useState<QuickRangeKey | null>(null);
  const [filterErrorMessage, setFilterErrorMessage] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedIncident, setSelectedIncident] = useState<IncidentDetailPanelData | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const hasActiveFilters = Boolean(
    draftStartDate || draftEndDate || draftDecision !== "all" || draftAlertLevel !== "all",
  );
  const hasTimeRange = Boolean(appliedStartDate || appliedEndDate);
  const rangeValidationMessage = getRangeValidationMessage(draftStartDate, draftEndDate);

  useEffect(() => {
    const controller = new AbortController();

    async function loadIncidents() {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const fetchIncidents = activeView === "raw" ? getRawIncidents : getIncidents;
        const response = await fetchIncidents({
          limit: hasTimeRange ? RANGE_LIMIT : DEFAULT_LIMIT,
          decision: appliedDecision !== "all" ? appliedDecision : undefined,
          fromTs: formatApiDateTime(appliedStartDate),
          toTs: formatApiDateTime(appliedEndDate),
          signal: controller.signal,
        });

        setIncidents(response);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        setErrorMessage(error instanceof Error ? error.message : "Failed to load incidents.");
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void loadIncidents();

    return () => {
      controller.abort();
    };
  }, [activeView, appliedDecision, appliedEndDate, appliedStartDate, hasTimeRange]);

  const tableRows = useMemo(
    () => incidents.map((incident) => mapIncidentResponseToRow(incident)),
    [incidents],
  );

  const filteredRows = useMemo(() => {
    return tableRows.filter((row) => {
      const matchesAlertLevel = appliedAlertLevel === "all" || row.alertLevel === appliedAlertLevel;
      return matchesAlertLevel;
    });
  }, [appliedAlertLevel, tableRows]);

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
    const incident = incidents.find((entry) => getIncidentDisplayId(entry) === row.incidentId);

    if (!incident) {
      return;
    }

    setSelectedIncident(mapIncidentResponseToDetail(incident));
    setIsDetailOpen(true);
  };

  const applyFilters = () => {
    if (rangeValidationMessage) {
      setFilterErrorMessage(rangeValidationMessage);
      return;
    }

    setFilterErrorMessage(null);
    setAppliedStartDate(draftStartDate);
    setAppliedEndDate(draftEndDate);
    setAppliedDecision(draftDecision);
    setAppliedAlertLevel(draftAlertLevel);
    setActiveQuickRange(null);
    setCurrentPage(1);
  };

  const applyQuickRange = (range: QuickRangeKey) => {
    const nextRange = getQuickRange(range);
    setDraftStartDate(nextRange.start);
    setDraftEndDate(nextRange.end);
    setFilterErrorMessage(null);
    setAppliedStartDate(nextRange.start);
    setAppliedEndDate(nextRange.end);
    setActiveQuickRange(range);
    setCurrentPage(1);
  };

  const resetFilters = () => {
    setDraftStartDate(undefined);
    setDraftEndDate(undefined);
    setDraftDecision("all");
    setDraftAlertLevel("all");
    setAppliedStartDate(undefined);
    setAppliedEndDate(undefined);
    setAppliedDecision("all");
    setAppliedAlertLevel("all");
    setActiveQuickRange(null);
    setFilterErrorMessage(null);
    setCurrentPage(1);
  };

  const getQuickRangeButtonClasses = (range: QuickRangeKey): string =>
    activeQuickRange === range
      ? "border-slate-900 bg-slate-900 text-slate-50 hover:bg-slate-900 hover:text-slate-50 dark:border-slate-100 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-100 dark:hover:text-slate-900"
      : "border-slate-300 bg-slate-50 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700";

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

        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              setActiveView("aggregated");
              setCurrentPage(1);
              setSelectedIncident(null);
              setIsDetailOpen(false);
            }}
            className={getIncidentViewButtonClasses("aggregated", activeView)}
          >
            Aggregated
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              setActiveView("raw");
              setCurrentPage(1);
              setSelectedIncident(null);
              setIsDetailOpen(false);
            }}
            className={getIncidentViewButtonClasses("raw", activeView)}
          >
            Raw Frames
          </Button>
        </div>

        <div className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          {filterErrorMessage ? (
            <div className="mb-4 rounded-sm border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-700/60 dark:bg-amber-900/20 dark:text-amber-200">
              {filterErrorMessage}
            </div>
          ) : null}

          <div className="mb-4 flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Quick Ranges
            </span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => applyQuickRange("lastHour")}
              className={getQuickRangeButtonClasses("lastHour")}
            >
              Last 1 Hour
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => applyQuickRange("today")}
              className={getQuickRangeButtonClasses("today")}
            >
              Today
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => applyQuickRange("last7Days")}
              className={getQuickRangeButtonClasses("last7Days")}
            >
              Last 7 Days
            </Button>
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
            <DateTimePicker
              label="Start"
              value={draftStartDate}
              onChange={(value) => {
                setDraftStartDate(value);
                setFilterErrorMessage(null);
              }}
              onCommit={applyFilters}
            />

            <DateTimePicker
              label="End"
              value={draftEndDate}
              onChange={(value) => {
                setDraftEndDate(value);
                setFilterErrorMessage(null);
              }}
              onCommit={applyFilters}
            />

            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Decision
              <Select
                value={draftDecision}
                onValueChange={(value) => {
                  const nextValue = value as (typeof ALL_DECISIONS)[number];
                  setDraftDecision(nextValue);
                  setAppliedDecision(nextValue);
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
                value={draftAlertLevel}
                onValueChange={(value) => {
                  const nextValue = value as (typeof ALL_ALERT_LEVELS)[number];
                  setDraftAlertLevel(nextValue);
                  setAppliedAlertLevel(nextValue);
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
                onClick={resetFilters}
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

          <Table className="min-w-[960px] text-left text-sm text-slate-700 dark:text-slate-200">
            <TableHeader className="text-slate-500 dark:text-slate-400">
              {activeView === "aggregated" ? (
                <TableRow className="border-b border-slate-300 hover:bg-transparent dark:border-slate-700">
                  <TableHead className="px-2 py-3 font-semibold">Event Start</TableHead>
                  <TableHead className="px-2 py-3 font-semibold">Last Seen</TableHead>
                  <TableHead className="px-2 py-3 font-semibold">Frames</TableHead>
                  <TableHead className="px-2 py-3 font-semibold">Drone Frames</TableHead>
                  <TableHead className="px-2 py-3 font-semibold">Max Confidence</TableHead>
                  <TableHead className="px-2 py-3 font-semibold">Avg Confidence</TableHead>
                  <TableHead className="px-2 py-3 font-semibold">Alert Level</TableHead>
                </TableRow>
              ) : (
                <TableRow className="border-b border-slate-300 hover:bg-transparent dark:border-slate-700">
                  <TableHead className="px-2 py-3 font-semibold">Detected At</TableHead>
                  <TableHead className="px-2 py-3 font-semibold">Decision</TableHead>
                  <TableHead className="px-2 py-3 font-semibold">Alert Level</TableHead>
                  <TableHead className="px-2 py-3 font-semibold">Fused Confidence</TableHead>
                </TableRow>
              )}
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
                  {activeView === "aggregated" ? (
                    <>
                      <TableCell className="px-2 py-3">
                        {formatDisplayTimestamp(row.detectedAt)}
                      </TableCell>
                      <TableCell className="px-2 py-3">
                        {row.lastSeenAt ? formatDisplayTimestamp(row.lastSeenAt) : "--"}
                      </TableCell>
                      <TableCell className="px-2 py-3">{formatCount(row.frameCount)}</TableCell>
                      <TableCell className="px-2 py-3">
                        {formatCount(row.droneFrameCount)}
                      </TableCell>
                      <TableCell className="px-2 py-3">
                        {formatConfidencePercentage(row.fusedConfidence)}
                      </TableCell>
                      <TableCell className="px-2 py-3">
                        {row.avgFusedConfidence == null
                          ? "--"
                          : formatConfidencePercentage(row.avgFusedConfidence)}
                      </TableCell>
                      <TableCell className="px-2 py-3">
                        <Badge
                          className={`px-3 py-1 text-sm font-semibold uppercase ${getAlertLevelBadgeClasses(row.alertLevel)}`}
                        >
                          {row.alertLevel}
                        </Badge>
                      </TableCell>
                    </>
                  ) : (
                    <>
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
                      <TableCell className="px-2 py-3">
                        {formatConfidencePercentage(row.fusedConfidence)}
                      </TableCell>
                    </>
                  )}
                </TableRow>
              ))}
              {!isLoading && pagedRows.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell className="px-2 py-6 text-center text-slate-500 dark:text-slate-400" colSpan={activeView === "aggregated" ? 7 : 4}>
                    No incidents found for current filters.
                  </TableCell>
                </TableRow>
              ) : null}
              {isLoading ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell className="px-2 py-6 text-center text-slate-500 dark:text-slate-400" colSpan={activeView === "aggregated" ? 7 : 4}>
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
