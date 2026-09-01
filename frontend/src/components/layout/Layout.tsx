import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { MobileNav } from "./MobileNav";
import { Header } from "./Header";

export function Layout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-x-hidden p-4 pb-20 md:p-6 md:pb-6">
          <Outlet />
        </main>
        <MobileNav />
      </div>
    </div>
  );
}
