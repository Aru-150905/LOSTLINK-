import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t bg-muted/30">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-6 lg:px-8">
        <p className="text-sm text-muted-foreground">
          LostLink — College Festival Lost & Found Platform
        </p>
        <div className="flex gap-6 text-sm text-muted-foreground">
          <Link href="/upload/lost" className="hover:text-foreground">
            Report Lost
          </Link>
          <Link href="/upload/found" className="hover:text-foreground">
            Report Found
          </Link>
          <Link href="/my-items" className="hover:text-foreground">
            My Items
          </Link>
        </div>
      </div>
    </footer>
  );
}
