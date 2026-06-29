import * as React from "react";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@radix-ui/react-dialog";
import { Button } from "@/components/ui/button";

interface DialogProps extends React.ComponentProps<typeof Dialog> {
  children: React.ReactNode;
  trigger: React.ReactNode;
  title: string;
  description?: string;
  className?: string;
}

export function DialogComponent({
  className,
  children,
  trigger,
  title,
  description,
  ...props
}: DialogProps) {
  return (
    <div className={className}>
      <Dialog {...props}>
        <DialogTrigger asChild>{trigger}</DialogTrigger>
        <DialogContent className="sm:max-w-lg w-full sm:rounded-lg">
          <div className="space-y-2">
            <DialogTitle>{title}</DialogTitle>
            {description && (
              <DialogDescription className="text-muted-foreground">
                {description}
              </DialogDescription>
            )}
          </div>
          <div className="divide-y mt-4">
            <div className="py-4">{children}</div>
          </div>
          <div className="flex justify-end pt-4">
            <Button variant="outline" onClick={() => {}}>
              Cancel
            </Button>
            <Button>{/* Submit or action button would go here */}</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
