import { getStreamPlaybackUrl, X402PaymentRequiredError, type X402PaymentRequiredBody } from './stream';

export class PaymentStreamSession {
  private intervalId: number | null = null;
  private running = false;

  constructor(
    private readonly args: {
      token: string;
      contentId: string;
      pricePerSecondMinor: number;
      onTick: (deltaMinor: number) => void;
      onError: (message: string) => void;
      onPaymentRequired: (body: X402PaymentRequiredBody) => void;
    },
  ) {}

  async start(): Promise<void> {
    if (this.running) return;
    this.running = true;

    this.intervalId = window.setInterval(() => {
      this.tick().catch((e) => {
        this.args.onError(String(e));
        this.stop().catch(() => undefined);
      });
    }, 10_000);
  }

  private async tick(): Promise<void> {
    try {
      await getStreamPlaybackUrl(this.args.token, this.args.contentId);
      this.args.onTick(this.args.pricePerSecondMinor * 10);
    } catch (e) {
      if (e instanceof X402PaymentRequiredError) {
        this.args.onPaymentRequired(e.body);
      } else {
        this.args.onError(String(e));
      }
      await this.stop();
    }
  }

  async stop(): Promise<void> {
    if (!this.running) return;
    this.running = false;

    if (this.intervalId !== null) {
      window.clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
}
