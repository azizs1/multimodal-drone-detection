import { DashboardShell } from "@/components/layout/dashboard-shell";

type IncidentRow = {
  id: string;
  time: string;
  fusedConfidence: number;
  distanceFt: number;
  status: "Confirmed";
};

const INCIDENT_ROWS: IncidentRow[] = [
  { id: "#001", time: "14:32:07", fusedConfidence: 94, distanceFt: 14, status: "Confirmed" },
  { id: "#002", time: "14:33:16", fusedConfidence: 92, distanceFt: 15, status: "Confirmed" },
  { id: "#003", time: "14:35:44", fusedConfidence: 93, distanceFt: 14, status: "Confirmed" },
  { id: "#004", time: "14:37:09", fusedConfidence: 95, distanceFt: 13, status: "Confirmed" },
  { id: "#005", time: "14:40:51", fusedConfidence: 94, distanceFt: 14, status: "Confirmed" },
];

type ServiceStatus = "Connected" | "Unstable" | "Disconnected";

type ServiceItem = {
  name: string;
  status: ServiceStatus;
};

const SYSTEM_STATUS: ServiceItem[] = [
  { name: "RGB Cam", status: "Connected" },
  { name: "Thermal Cam", status: "Connected" },
  { name: "Jetson Nano", status: "Unstable" },
  { name: "Backend", status: "Connected" },
  { name: "WebSocket", status: "Disconnected" },
];

function VideoPanel({
  title,
  fps,
  resolution,
  boxColor,
  boxLabel,
}: {
  title: string;
  fps: string;
  resolution: string;
  boxColor: string;
  boxLabel: string;
}) {
  return (
    <section className="overflow-hidden rounded-sm border border-slate-200 bg-slate-50">
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2">
        <div className="flex items-center gap-2 text-slate-700">
          <span className="size-3 rounded-full bg-emerald-500" />
          <span className="text-base font-semibold">{title}</span>
        </div>
        <span className="text-sm font-medium text-slate-500">Live {fps} fps</span>
      </div>

      <div className="relative h-[280px] bg-slate-100 sm:h-[320px] lg:h-[360px]">
        <div className="absolute inset-0 flex items-center justify-center text-5xl text-slate-400">+</div>
        <div
          className={`absolute left-1/2 top-1/2 h-20 w-28 -translate-x-1/2 -translate-y-1/2 border-4 ${boxColor}`}
        >
          <span className={`absolute -left-1 -top-8 px-1 text-sm font-semibold ${boxColor}`}>
            {boxLabel}
          </span>
        </div>
      </div>

      <div className="px-3 py-2 text-sm text-slate-500">{resolution}</div>
    </section>
  );
}

function ConfidencePanel() {
  return (
    <section className="rounded-sm border border-slate-200 bg-slate-50 p-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Primary Metrics</p>
        <div className="mt-2 grid gap-3">
          <div className="rounded-md border border-cyan-100 bg-cyan-50/60 px-3 py-4 text-center">
            <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Fused Confidence</p>
            <p className="mt-1 text-4xl font-extrabold text-cyan-500">94%</p>
          </div>

          <div className="rounded-md border border-cyan-100 bg-cyan-50/60 px-3 py-4 text-center">
            <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Distance</p>
            <p className="mt-1 text-4xl font-extrabold text-cyan-500">~14ft</p>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Secondary Metrics
        </p>
        <div className="mt-2 rounded-md border border-slate-200 bg-slate-100 p-3 text-center">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-sm font-medium text-slate-500">Visual Confidence</p>
              <p className="mt-1 text-3xl font-bold text-slate-400">92%</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Thermal Confidence</p>
              <p className="mt-1 text-3xl font-bold text-slate-400">89%</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function RecentIncidentsTable() {
  return (
    <section className="rounded-sm border border-slate-200 bg-slate-50 p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Recent Incidents
      </h2>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-left text-sm text-slate-600">
          <thead className="text-slate-500">
            <tr className="border-b border-slate-200">
              <th className="px-3 py-3 font-semibold">ID</th>
              <th className="px-3 py-3 font-semibold">Time</th>
              <th className="px-3 py-3 font-semibold">Fused Confidence</th>
              <th className="px-3 py-3 font-semibold">Distance</th>
              <th className="px-3 py-3 font-semibold">Status</th>
              <th className="px-3 py-3 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {INCIDENT_ROWS.map((row) => (
              <tr key={row.id + row.time} className="border-b border-slate-200/80">
                <td className="px-3 py-3">{row.id}</td>
                <td className="px-3 py-3">{row.time}</td>
                <td className="px-3 py-3">{row.fusedConfidence}%</td>
                <td className="px-3 py-3">~{row.distanceFt}ft</td>
                <td className="px-3 py-3">
                  <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-700">
                    {row.status}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <button
                    type="button"
                    className="inline-flex items-center rounded-md border border-slate-300 bg-slate-100 px-4 py-1 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-1"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SystemStatusPanel() {
  const statusClasses: Record<ServiceStatus, string> = {
    Connected: "bg-emerald-500",
    Unstable: "bg-amber-400",
    Disconnected: "bg-rose-500",
  };

  const statusTextClasses: Record<ServiceStatus, string> = {
    Connected: "text-emerald-700",
    Unstable: "text-amber-700",
    Disconnected: "text-rose-700",
  };

  return (
    <section className="rounded-sm border border-slate-200 bg-slate-50 p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">System Status</h2>
      <ul className="mt-4 space-y-2 text-sm text-slate-700">
        {SYSTEM_STATUS.map((service) => (
          <li key={service.name} className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className={`size-3 rounded-full ${statusClasses[service.status]}`} />
              <span>{service.name}</span>
            </div>
            <span className={`text-sm font-semibold ${statusTextClasses[service.status]}`}>
              {service.status}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function LiveFeedPage() {
  return (
    <DashboardShell>
      <div className="grid gap-4 lg:grid-cols-5">
        <div className="space-y-4 lg:col-span-4">
          <div className="grid gap-4 xl:grid-cols-2">
            <VideoPanel
              title="Visual - RGB"
              fps="30"
              resolution="1920x1080 • RGB"
              boxColor="border-emerald-500 text-emerald-500"
              boxLabel="DRONE 94%"
            />
            <VideoPanel
              title="Thermal - IR"
              fps="30"
              resolution="640x480 • IR"
              boxColor="border-violet-400 text-violet-400"
              boxLabel="HEAT SIG 91%"
            />
          </div>

          <RecentIncidentsTable />
        </div>

        <div className="space-y-4">
          <ConfidencePanel />
          <SystemStatusPanel />
        </div>
      </div>
    </DashboardShell>
  );
}
