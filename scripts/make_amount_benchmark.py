"""Generate the gold-first amount benchmark manifests."""

from parcha.lab.amount_bench import write_amount_benchmarks


def main() -> int:
    totals = write_amount_benchmarks()
    print(
        f"estimates={totals['estimates']} (amounts={totals['amounts']}) "
        f"corrections={totals['corrections']} stress_amounts={totals['stress_amounts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
