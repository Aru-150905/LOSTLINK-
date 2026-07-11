"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Bell,
  LayoutDashboard,
  Link2,
  LogOut,
  Menu,
  Package,
  Search,
  Upload,
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { getNotifications } from "@/lib/api";
import { Button, buttonVariants } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/upload/lost", label: "Report Lost", icon: Search },
  { href: "/upload/found", label: "Report Found", icon: Upload },
  { href: "/my-items", label: "My Items", icon: Package },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/admin", label: "Admin", icon: LayoutDashboard },
];

export function Navbar() {
  const pathname = usePathname();
  const [user, setUser] = useState<{ email?: string } | null>(null);
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => setUser(data.user));

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    if (pathname !== "/auth") {
      getNotifications()
        .then((data) => setUnread(data.unread_count))
        .catch(() => setUnread(0));
    }

    return () => listener.subscription.unsubscribe();
  }, [pathname]);

  const handleSignOut = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = "/auth";
  };

  const NavContent = ({ mobile = false }: { mobile?: boolean }) => (
    <>
      {navLinks.map(({ href, label, icon: Icon }) => {
        if (href === "/admin" && !user) return null;
        const active = pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
              mobile && "w-full"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
            {href === "/notifications" && unread > 0 && (
              <Badge variant="destructive" className="ml-auto h-5 min-w-5 px-1">
                {unread}
              </Badge>
            )}
          </Link>
        );
      })}
    </>
  );

  return (
    <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Link2 className="h-5 w-5" />
          </div>
          <span className="hidden sm:inline">LostLink</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          <NavContent />
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          {user ? (
            <Button variant="outline" size="sm" onClick={handleSignOut}>
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </Button>
          ) : (
            <Button asChild size="sm">
              <Link href="/auth">Sign in</Link>
            </Button>
          )}

          <Sheet>
            <SheetTrigger
              className={cn(buttonVariants({ variant: "ghost", size: "icon" }), "md:hidden")}
            >
              <Menu className="h-5 w-5" />
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <div className="mt-8 flex flex-col gap-2">
                <NavContent mobile />
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
