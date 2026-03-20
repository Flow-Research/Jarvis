import { z } from "zod";

type ZodNamespace = typeof z & {
  literal?: (value: string | number | boolean | null) => unknown;
};

const createLiteral = (value: string): z.ZodType<string> => {
  const zod = z as ZodNamespace;
  if (typeof zod.literal === "function") {
    return zod.literal(value) as z.ZodType<string>;
  }

  return z.custom<string>((candidate): candidate is string => candidate === value, {
    message: `Expected value "${String(value)}"`,
  });
};

const AllowDenyActionSchema = z.union([createLiteral("allow"), createLiteral("deny")]);

const AllowDenyChatTypeSchema = z
  .union([
    createLiteral("direct"),
    createLiteral("group"),
    createLiteral("channel"),
    /** @deprecated Use `direct` instead. Kept for backward compatibility. */
    createLiteral("dm"),
  ])
  .optional();

export function createAllowDenyChannelRulesSchema() {
  return z
    .object({
      default: AllowDenyActionSchema.optional(),
      rules: z
        .array(
          z
            .object({
              action: AllowDenyActionSchema,
              match: z
                .object({
                  channel: z.string().optional(),
                  chatType: AllowDenyChatTypeSchema,
                  keyPrefix: z.string().optional(),
                  rawKeyPrefix: z.string().optional(),
                })
                .strict()
                .optional(),
            })
            .strict(),
        )
        .optional(),
    })
    .strict()
    .optional();
}
