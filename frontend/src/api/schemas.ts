/**
 * Schemas Zod espelhando os models Pydantic do backend.
 *
 * Servem dois propósitos:
 *   1. Validação client-side antes de enviar (evita round-trip pro
 *      servidor só para receber um 422).
 *   2. Inferência de tipos TS — as `interface`s em client.ts ficam
 *      redundantes mas preservadas por compat; aqui derivamos `type`
 *      equivalentes com `z.infer`.
 *
 * Mantemos as regras alinhadas com `backend/schemas.py`. Se divergirem,
 * o backend continua sendo a fonte da verdade (422 eventual).
 */

import { z } from 'zod';

// ---------------------------------------------------------------------------
// Inputs
// ---------------------------------------------------------------------------

export const usuarioInSchema = z.object({
  nome: z
    .string()
    .trim()
    .min(3, 'Nome precisa ter ao menos 3 caracteres')
    .max(80, 'Nome muito longo (máx. 80)'),
  email: z.string().trim().email('E-mail inválido'),
});
export type UsuarioInput = z.infer<typeof usuarioInSchema>;

export const sessaoInSchema = z.object({
  usuario_id: z.number().int().positive(),
  url: z
    .string()
    .trim()
    .min(8, 'URL muito curta')
    .max(2048, 'URL muito longa')
    .refine(
      (v) => v.startsWith('http://') || v.startsWith('https://'),
      'Use http:// ou https://',
    ),
  headless: z.boolean(),
});
export type SessaoInput = z.infer<typeof sessaoInSchema>;

export const selecaoInSchema = z.object({
  xpath: z.string().min(1, 'XPath vazio'),
  text: z.string().min(1, 'Valor vazio'),
});
export type SelecaoInput = z.infer<typeof selecaoInSchema>;

// ---------------------------------------------------------------------------
// Helpers de validação
// ---------------------------------------------------------------------------

/**
 * Pega o primeiro erro do ZodError num formato pronto para toast/label.
 * Retorna `null` se o objeto validou.
 */
export function primeiraMensagem<T>(
  schema: z.ZodType<T>,
  valor: unknown,
): string | null {
  const parsed = schema.safeParse(valor);
  if (parsed.success) return null;
  return parsed.error.issues[0]?.message ?? 'Valor inválido';
}
