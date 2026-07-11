import Link from "next/link";
import {
  ArrowRight,
  Brain,
  ImageIcon,
  MapPin,
  Shield,
  Sparkles,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const features = [
  {
    icon: Brain,
    title: "AI-Powered Matching",
    description:
      "CLIP image embeddings and Sentence Transformers compare your items against thousands of entries automatically.",
  },
  {
    icon: ImageIcon,
    title: "Visual Similarity Search",
    description:
      "Upload a photo and our engine finds visually similar items using cosine similarity on vector embeddings.",
  },
  {
    icon: MapPin,
    title: "Smart Metadata Scoring",
    description:
      "Location proximity, time windows, and category matching boost confidence for the best results.",
  },
  {
    icon: Shield,
    title: "Secure Claims",
    description:
      "Claim requests go through admin review to prevent fraudulent pickups and protect everyone's items.",
  },
];

const steps = [
  { step: "1", title: "Report", desc: "Upload a lost or found item with details and optional photo" },
  { step: "2", title: "Match", desc: "AI generates embeddings and searches the opposite category" },
  { step: "3", title: "Connect", desc: "Review matches, submit a claim, and get your item back" },
];

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="relative overflow-hidden border-b">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/10" />
        <div className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border bg-muted/50 px-4 py-1.5 text-sm">
              <Sparkles className="h-4 w-4 text-amber-500" />
              College Festival Lost & Found
            </div>
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
              Reunite with what you&apos;ve{" "}
              <span className="text-primary">lost</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground sm:text-xl">
              LostLink uses cutting-edge AI to match lost and found items through
              image similarity, text understanding, and smart metadata scoring.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Button asChild size="lg" className="w-full sm:w-auto">
                <Link href="/upload/lost">
                  Report Lost Item
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
                <Link href="/upload/found">Report Found Item</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="mb-12 text-center">
          <h2 className="text-3xl font-bold">How it works</h2>
          <p className="mt-2 text-muted-foreground">
            Three simple steps to get your belongings back
          </p>
        </div>
        <div className="grid gap-8 md:grid-cols-3">
          {steps.map(({ step, title, desc }) => (
            <div key={step} className="relative text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                {step}
              </div>
              <h3 className="text-xl font-semibold">{title}</h3>
              <p className="mt-2 text-muted-foreground">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="border-t bg-muted/30">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold">Powered by AI</h2>
            <p className="mt-2 text-muted-foreground">
              70% image · 20% text · 10% metadata scoring
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ icon: Icon, title, description }) => (
              <Card key={title} className="border-0 bg-background shadow-sm">
                <CardHeader>
                  <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <CardTitle className="text-lg">{title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <Card className="overflow-hidden border-primary/20 bg-gradient-to-r from-primary/5 to-primary/10">
          <CardContent className="flex flex-col items-center gap-6 p-8 text-center sm:p-12">
            <Zap className="h-10 w-10 text-primary" />
            <div>
              <h2 className="text-2xl font-bold sm:text-3xl">
                Ready to find your item?
              </h2>
              <p className="mt-2 text-muted-foreground">
                Join LostLink at the festival and let AI do the searching for you.
              </p>
            </div>
            <Button asChild size="lg">
              <Link href="/auth">Get started — it&apos;s free</Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
