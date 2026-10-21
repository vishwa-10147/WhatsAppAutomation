import { Construction } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'

export function FeaturePlaceholder({ title, description }: { title: string; description: string }) {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="mt-1 text-muted-foreground">This module is planned and is not connected to production data yet.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Construction className="h-5 w-5" /> In development</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No sample records or production metrics are displayed here. The module will become available after its API and workflow milestone is implemented and verified.</p>
        </CardContent>
      </Card>
    </div>
  )
}
