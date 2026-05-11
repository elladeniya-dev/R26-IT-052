from collectors.public_fashion_page_collector import collect_all_public_fashion_sources


def main():
    result = collect_all_public_fashion_sources()

    summary = result["summary"]

    print("\nCollection completed.")
    print(f"Total sources: {summary['total_sources']}")
    print(f"Successful sources: {summary['successful_sources']}")
    print(f"Failed sources: {summary['failed_sources']}")
    print(f"Total raw products: {summary['total_raw_products']}")
    print(f"Total trend observations: {summary['total_trend_observations']}")
    print(f"Combined raw output: {summary['combined_raw_products_file']}")
    print(
        f"Combined observations output: {summary['combined_trend_observations_file']}"
    )

    print("\nSource summary:")

    for source in summary["sources"]:
        print(
            f"- {source['source_name']} | "
            f"status: {source['status']} | "
            f"products: {source['raw_product_count']} | "
            f"observations: {source['trend_observation_count']}"
        )

    print("\nTop mapped observations:")

    for observation in result["observations"][:15]:
        print(
            f"- {observation['source_name']} | "
            f"{observation['attribute_type']} | "
            f"{observation['attribute_value']} | "
            f"mentions: {observation['mention_count']} | "
            f"avg rank: {observation['rank_position']}"
        )


if __name__ == "__main__":
    main()
