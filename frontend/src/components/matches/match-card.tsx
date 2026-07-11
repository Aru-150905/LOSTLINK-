"use client";

import Image from "next/image";
import Link from "next/link";
import { format } from "date-fns";
import { MapPin, Calendar } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { Item, MatchResult } from "@/types";

interface MatchCardProps {
  match: MatchResult;
  onClaim?: (itemId: string) => void;
}

export function MatchCard({ match, onClaim }: MatchCardProps) {
  const item = match.matched_item;
  const confidence = Math.round(match.confidence_score * 100);

  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-md">
      {item?.image_url && (
        <div className="relative aspect-video w-full bg-muted">
          <Image
            src={item.image_url}
            alt={item.title}
            fill
            className="object-cover"
            unoptimized
          />
        </div>
      )}
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-lg">{item?.title ?? "Unknown item"}</CardTitle>
            <CardDescription className="mt-1 line-clamp-2">
              {item?.description || "No description provided"}
            </CardDescription>
          </div>
          <Badge
            variant={confidence >= 70 ? "default" : confidence >= 40 ? "secondary" : "outline"}
          >
            {confidence}% match
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Confidence</span>
            <span>{confidence}%</span>
          </div>
          <Progress value={confidence} className="h-2" />
        </div>

        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <div className="rounded-lg bg-muted p-2">
            <p className="font-medium">{Math.round(match.image_score * 100)}%</p>
            <p className="text-muted-foreground">Image</p>
          </div>
          <div className="rounded-lg bg-muted p-2">
            <p className="font-medium">{Math.round(match.text_score * 100)}%</p>
            <p className="text-muted-foreground">Text</p>
          </div>
          <div className="rounded-lg bg-muted p-2">
            <p className="font-medium">{Math.round(match.metadata_score * 100)}%</p>
            <p className="text-muted-foreground">Meta</p>
          </div>
        </div>

        {item && (
          <div className="space-y-1 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              {item.location}
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              {format(new Date(item.item_timestamp), "PPp")}
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="gap-2">
        {item && (
          <>
            <Button asChild variant="outline" className="flex-1">
              <Link href={`/matches/${match.item_id}`}>View details</Link>
            </Button>
            {onClaim && (
              <Button className="flex-1" onClick={() => onClaim(item.id)}>
                Claim item
              </Button>
            )}
          </>
        )}
      </CardFooter>
    </Card>
  );
}

interface ItemCardProps {
  item: Item;
  actions?: React.ReactNode;
}

export function ItemCard({ item, actions }: ItemCardProps) {
  const statusColors: Record<string, string> = {
    active: "default",
    matched: "secondary",
    claimed: "outline",
    returned: "secondary",
    resolved: "secondary",
  };

  return (
    <Card className="overflow-hidden">
      {item.image_url && (
        <div className="relative aspect-video w-full bg-muted">
          <Image
            src={item.image_url}
            alt={item.title}
            fill
            className="object-cover"
            unoptimized
          />
        </div>
      )}
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg">{item.title}</CardTitle>
          <div className="flex gap-1">
            <Badge variant={item.type === "lost" ? "destructive" : "default"}>
              {item.type}
            </Badge>
            <Badge variant={statusColors[item.status] as "default"}>
              {item.status}
            </Badge>
          </div>
        </div>
        <CardDescription className="line-clamp-2">
          {item.description || "No description"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-1 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4" />
          {item.location}
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4" />
          {format(new Date(item.item_timestamp), "PPp")}
        </div>
      </CardContent>
      {actions && <CardFooter>{actions}</CardFooter>}
    </Card>
  );
}
