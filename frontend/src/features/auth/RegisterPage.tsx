import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { MessageSquare, Mail, Lock, User, Building2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card'
import { Alert, AlertDescription } from '@/components/ui/Alert'
import { useRegister } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'

const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(12, 'Password must be at least 12 characters'),
  confirmPassword: z.string(),
  full_name: z.string().min(1, 'Full name is required').max(255).optional(),
  organization_name: z.string().min(1, 'Organization name is required').max(255),
  organization_slug: z.string().min(1, 'Organization slug is required').max(100).regex(/^[a-z0-9-]+$/, 'Slug can only contain lowercase letters, numbers, and hyphens'),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
})

type RegisterForm = z.infer<typeof registerSchema>

export function RegisterPage() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const { mutate: register, isPending } = useRegister()

  const {
    register: registerForm,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      full_name: '',
      organization_name: '',
      organization_slug: '',
    },
  })

  const onSubmit = async (data: RegisterForm) => {
    setError(null)
    const { confirmPassword, ...submitData } = data
    register(submitData, {
      onSuccess: () => {
        navigate('/')
      },
      onError: (err: Error) => {
        setError(err.message || 'Registration failed. Please try again.')
      },
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/50 px-4 py-12">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
            <MessageSquare className="h-7 w-7 text-primary-foreground" />
          </div>
          <CardTitle className="text-2xl">Create your account</CardTitle>
          <CardDescription>Start automating WhatsApp messages today</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  className="pl-10"
                  {...registerForm('email')}
                  disabled={isPending}
                  aria-invalid={errors.email ? 'true' : 'false'}
                />
              </div>
              {errors.email && <p className="text-sm text-destructive" role="alert">{errors.email.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name (optional)</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="full_name"
                  type="text"
                  placeholder="John Doe"
                  className="pl-10"
                  {...registerForm('full_name')}
                  disabled={isPending}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  className="pl-10"
                  {...registerForm('password')}
                  disabled={isPending}
                  aria-invalid={errors.password ? 'true' : 'false'}
                />
              </div>
              {errors.password && <p className="text-sm text-destructive" role="alert">{errors.password.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  className="pl-10"
                  {...registerForm('confirmPassword')}
                  disabled={isPending}
                  aria-invalid={errors.confirmPassword ? 'true' : 'false'}
                />
              </div>
              {errors.confirmPassword && <p className="text-sm text-destructive" role="alert">{errors.confirmPassword.message}</p>}
            </div>

            <Separator className="my-4" />

            <div className="space-y-2">
              <Label htmlFor="organization_name">Organization Name</Label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="organization_name"
                  type="text"
                  placeholder="Acme Inc."
                  className="pl-10"
                  {...registerForm('organization_name')}
                  disabled={isPending}
                  aria-invalid={errors.organization_name ? 'true' : 'false'}
                />
              </div>
              {errors.organization_name && <p className="text-sm text-destructive" role="alert">{errors.organization_name.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="organization_slug">Organization Slug</Label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="organization_slug"
                  type="text"
                  placeholder="acme-inc"
                  className="pl-10 lowercase"
                  {...registerForm('organization_slug')}
                  disabled={isPending}
                  aria-invalid={errors.organization_slug ? 'true' : 'false'}
                  aria-describedby="slug-hint"
                />
              </div>
              <p id="slug-hint" className="text-sm text-muted-foreground">
                Used in URLs. Lowercase letters, numbers, and hyphens only.
              </p>
              {errors.organization_slug && <p className="text-sm text-destructive" role="alert">{errors.organization_slug.message}</p>}
            </div>

            <Button type="submit" className="w-full" loading={isPending}>
              Create account
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline font-medium">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}

function Separator({ className }: { className?: string }) {
  return <hr className={cn('border-border', className)} />
}
