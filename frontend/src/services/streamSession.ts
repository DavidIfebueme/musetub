import { closeChannel, openChannel, tickChannel } from './payments';

export class PaymentStreamSession {
  private channelId: string | null = null;
  private intervalId: number | null = null;
  private running = false;

  constructor(
    private readonly args: {
      token: string;
      contentId: string;
      pricePerSecondMinor: number;
      onTick: (deltaMinor: number) => void;
      onError: (message: string) => void;
    },
  ) {}

  async start(): Promise<void> {
    if (this.running) return;
    this.running = true;

    const opened = await openChannel(this.args.token, this.args.contentId);
    this.channelId = opened.id;

    this.intervalId = window.setInterval(() => {
      this.tick().catch((e) => {
        this.args.onError(String(e));
        this.stop().catch(() => undefined);
      });
    }, 10_000);

    await this.tick();
  }

  private async tick(): Promise<void> {
    if (!this.channelId) return;
    const resp = await tickChannel(this.args.token, this.channelId);
    const delta = this.args.pricePerSecondMinor * resp.tick_seconds;
    if (resp.tick_seconds > 0) {
      this.args.onTick(delta);
    }
  }

  async stop(): Promise<void> {
    if (!this.running) return;
    this.running = false;

    if (this.intervalId !== null) {
      window.clearInterval(this.intervalId);
      this.intervalId = null;
    }

    if (this.channelId) {
      try {
        await closeChannel(this.args.token, this.channelId);
      } catch (e) {
        this.args.onError(String(e));
      }
      this.channelId = null;
    }
  }
}
