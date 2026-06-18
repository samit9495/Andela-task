import { NavLink, Outlet } from "react-router-dom";

const links = [
  { to: "/", label: "Overview", end: true },
  { to: "/incidents", label: "Incident Center", end: false },
  { to: "/topology", label: "Topology", end: false },
];

export function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>🐕 Watchdog</h1>
        <nav className="nav">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end}>
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
