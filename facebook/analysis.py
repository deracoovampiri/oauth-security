from domain import FacebookDomains
from utility.utility import get_errors, get_attacks
from collections import Counter
from tabulate import tabulate
import json
from tinydb import TinyDB, Query
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from matplotlib_venn import venn3
from utility.facebook import get_version, get_facebook, get_domain_flow, \
    get_state, get_states, get_display, get_vulnerable, is_vulnerable

db = FacebookDomains("data/facebook")


# Clean the list of domains removing the errors
def remove_errors(filename):
    errors = get_errors("registration")
    database = TinyDB(f"data/{filename}.json", indent=4)
    cleaned = TinyDB(f"data/{filename}-cleaned.json", indent=4)
    for domain in database.all():
        # Add the domains without errors
        if domain["domain"] not in errors:
            cleaned.insert(domain)


# Include the registration errors in the database
def add_registration_errors():
    errors = get_errors("registration")
    for domain in db.all():
        has_error = domain["domain"] in errors
        db.save_value(domain, "registration_error", has_error)


# Get the list of state parameters
def get_all_states(domains):
    return [get_state(x) for x in domains]


# Print the lengths of the state parameters
def print_state_lengths(domains, bins=10):
    states = get_all_states(domains)
    lengths = [len(x) for x in states if x]
    counter = Counter(lengths)

    keys = ["0"] + [f"$2^{x}$" for x in range(bins)]
    values = [len([x for x in states if not x])]

    for i in range(bins):
        value = sum([x[1] for x in counter.items() if 2**i <= x[0] < 2**(i+1)])
        print(f"Range {2**i} <= x < {2**(i+1)} => {value}")
        values.append(value)

    more = sum([x[1] for x in counter.items() if x[0] >= 2**bins])
    print(f"Range x >= {2**bins} => {more}")
    print(counter.most_common())
    values[bins-1] += more

    # Plot the histogram with the buckets data
    plot_state_lengths(keys, values)


# Plot the lengths of the state parameters
def plot_state_lengths(labels, values):
    figure, ax = plt.subplots(1, 1, figsize=(6, 4))

    ax.spines["right"].set_color(None)
    ax.spines["top"].set_color(None)
    ax.set_axisbelow(True)
    ax.tick_params(direction="in", length=0)
    plt.grid(axis="y", color="#dddddd")

    # Plot the histogram with the buckets data
    plt.bar(labels, values, color="w", edgecolor="k", width=0.6)
    ax.set_ylabel("Number of states")
    ax.set_xlabel("Number of characters per state")
    ax.set_yscale("log", basey=2)

    figure.tight_layout()
    figure.savefig("figures/state_length.png", format="png")
    figure.savefig("figures/state_length.eps", format="eps")
    plt.show()


# Print information about Facebook dialog version
def get_api_versions(domains):
    versions, vulnerable = [], []
    for domain in domains:
        version = get_version(domain)
        major_version = f"v{int(version)}" if version else "-"
        versions.append(major_version)
        if is_vulnerable(domain):
            vulnerable.append(major_version)

    version_counter = Counter(versions)
    vulnerable_counter = Counter(vulnerable)
    print(version_counter.most_common())

    items = sorted(version_counter.items())
    labels = [x[0] for x in items]
    values = [x[1] for x in items]
    values_v = [vulnerable_counter[x] for x in labels]

    # Plot the vulnerabilities
    figure, ax = plt.subplots(1, 1, figsize=(8, 4))
    ax.spines["right"].set_color(None)
    ax.spines["top"].set_color(None)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    plt.grid(axis="y", color="#dddddd")

    x = np.arange(len(labels))
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    width = 0.35

    # Plot the histograms with the buckets data
    r1 = ax.bar(x - width / 2, values, width, label="Domains", color="w", edgecolor="k")
    r2 = ax.bar(x + width / 2, values_v, width, label="Vulnerable", color="#b2bec3", edgecolor="k")

    # Attach a text label above each bar, displaying its height
    def auto_label(bars):
        for bar in bars:
            h, w = bar.get_height(), bar.get_width()
            ax.annotate("{}".format(h), xy=(bar.get_x() + w / 2, h), xytext=(0, 3),
                        textcoords="offset points", ha="center", va="bottom")
    auto_label(r1)
    auto_label(r2)

    # Add labels on the axis and the legend
    ax.set_ylabel("Number of domains")
    ax.set_xlabel("Facebook Graph API major version")
    ax.legend()

    figure.tight_layout()
    figure.savefig("figures/api_version.png", format="png")
    figure.savefig("figures/api_version.eps", format="eps")
    plt.show()


# Print the table data in the format X (Y%)
def print_data(count, total, precision=1):
    percentage = "{0:.{p}f}".format(count*100/total, p=precision)
    return f"{count} ({percentage}%)"


# Get the display property for Facebook logins
def get_display_mode(domains):
    display_mode, popup = [], []
    for domain in domains:
        display = get_display(domain)
        display_mode.append(display)
        if display == "popup":
            popup.append(domain)
    print(Counter(display_mode).most_common())
    analyze_vulnerabilities(domains=popup)
    for domain in popup:
        print(f"\n{domain}")
        states = get_states(domain)
        print(states)


# Plot the excluded domains
def plot_exclusions():
    registration_errors = len(db.get_registration_errors())
    js_sdk = len(db.get_js_sdk())
    authorization_errors = len(db.get_authorization_errors())
    login_errors = len(db.get_login_incomplete())
    domains = len(db.get_domains())

    sizes = [registration_errors, js_sdk, authorization_errors, login_errors, domains]
    colors = ['#ff7675', '#fab1a0', '#ffeaa7', '#fdcb6e', "#74b9ff"]
    labels = [f"Registration errors ({registration_errors})",
              f"JavaScript SDK ({js_sdk})",
              f"Authorization errors ({authorization_errors})",
              f"Login errors ({login_errors})",
              f"Valid websites ({domains})"]

    figure, texts, auto_text = plt.pie(sizes, autopct="%1.1f%%", colors=colors, startangle=260)

    plt.legend(figure, labels, bbox_to_anchor=(1, 0.5), loc="center right", fontsize=10, prop={'size': 12}, bbox_transform=plt.gcf().transFigure)
    plt.subplots_adjust(left=0.0, bottom=0.1, right=0.6)
    # plt.legend(figure, labels, loc="center left", bbox_to_anchor=(0.7, 0.75), prop={'size': 10}, framealpha=1)
    plt.savefig("figures/exclusions.png", format="png", bbox_inches="tight")
    plt.savefig("figures/exclusions.eps", format="eps", bbox_inches="tight", transparent=True)
    plt.show()


# Get the property values for the given domains
def get_property_values(domains, _property):
    values = []
    for domain in domains:
        facebook = get_facebook(domain)
        values.append(facebook.get(_property) if _property in facebook else None)
    return Counter(values).most_common()


# Analyze the property values of the given domains
def analyze_property_values(domains):
    properties = ["registration_error", "victim_marker", "attacker_marker",
                  "authorization_error", "authorization_response"]
    for _property in properties:
        values = get_property_values(domains, _property)
        print(f"{_property}: {values}")


# Analyze the vulnerable domains
def analyze_vulnerabilities(domains=None, attacks=None):
    attacks = attacks or get_attacks()
    domains = domains or db.get_attack_domains(state=None)
    vulnerable = len(get_vulnerable(domains))

    results = [json.dumps([is_vulnerable(y, [x]) for x in attacks]) for y in domains]
    table = [["#"] + attacks + ["Domains"]]
    row_number = 0
    for item in Counter(results).most_common():
        row_number += 1
        data = [row_number]
        data.extend([x for x in json.loads(item[0])])
        data.append(print_data(item[1], len(domains)))  # vulnerable))
        table.append(data)

    data = ["Tot"] + [str(len(get_vulnerable(domains, [x]))) for x in attacks] + [str(len(domains))]
    table.append(data)

    print(tabulate(table, headers="firstrow", tablefmt="latex"))

    print(f"\nTotal domains: {len(domains)}")
    print(f"Vulnerable domains: {vulnerable}")
    print([{x: len(get_vulnerable(domains, [x]))} for x in attacks])


# Get the domains using the same value for state in the attacks
def get_constant_state_domains(domains, attacks=2):
    constant = []
    for domain in domains:
        states = get_states(domain)
        if [x for x, c in Counter(states).items() if c >= attacks]:
            constant.append(domain)
    return constant


# Analyze the domains using the same value for state in the attacks
def analyze_constant_state(domains, attacks=2):
    constant = []
    for domain in domains:
        states = get_states(domain)
        repeated = [(x, c) for x, c in Counter(states).items() if c >= attacks]
        if repeated:
            print(domain["domain"])
            for state in repeated:
                print(f"\trepeats \"{state[0]}\" {state[1]} times")
            constant.append(domain)

    print(f"Domains with constant state: {len(constant)}\n")
    analyze_vulnerabilities(domains=constant, attacks=get_attacks("3"))


# Analyze the vulnerable domain in presence/absence of state
def analyze_state_presence():
    domains = db.get_attack_domains()
    yes = db.get_attack_domains(state=True)
    no = db.get_attack_domains(state=False)
    count, yes_count, no_count = len(domains), len(yes), len(no)
    table = [["State", "Domains", "Vulnerable"]]
    table.append(["Present", print_data(yes_count, count), print_data(len(get_vulnerable(yes)), yes_count)])
    table.append(["Absent", print_data(no_count, count), print_data(len(get_vulnerable(no)), no_count)])
    table.append(["Total", count, print_data(len(get_vulnerable(domains)), count)])
    print(tabulate(table, headers="firstrow", tablefmt="latex"))


# Plot the vulenable domains in the different configurations
def plot_vulnerable_configurations(domains, attacks="0,1,2,3,4"):
    # Get the vulnerabilities
    attack_ids = attacks.split(",")
    values_a, values_b, values_c = [], [], []
    labels = [f"Attack {x}" for x in attack_ids]

    for attack in attack_ids:
        values_a.append(len(get_vulnerable(domains, [f"{attack}a"])))
        values_b.append(len(get_vulnerable(domains, [f"{attack}b"])))
        values_c.append(len(get_vulnerable(domains, [f"{attack}c"])))

    # Plot the vulnerabilities
    figure, ax = plt.subplots(1, 1, figsize=(6, 5))
    ax.spines["right"].set_color(None)
    ax.spines["top"].set_color(None)
    ax.set_axisbelow(True)
    ax.tick_params(which="major", direction="in", length=5)
    plt.grid(axis="y", color="#dddddd")
    width = 0.25

    # Set position of bar on X axis
    xb = np.arange(len(labels))
    xa = [x - width for x in xb]
    xc = [x + 2*width for x in xa]

    # Plot the histograms with the buckets data
    r1 = ax.bar(xa, values_a, width, label="(a) No cookies", color="w", edgecolor="k")
    r2 = ax.bar(xb, values_b, width, label="(b) Visitor cookies", color="#dfe6e9", edgecolor="k")
    r3 = ax.bar(xc, values_c, width, label="(c) Authentication cookies", color="#b2bec3", edgecolor="k")

    # Add labels on the axis and the legend
    ax.set_ylabel("Vulnerable domains")
    ax.set_xticks(xb)
    ax.set_xticklabels(labels)
    ax.legend()

    # Attach a text label above each bar, displaying its height
    def auto_label(bars):
        for bar in bars:
            h, w = bar.get_height(), bar.get_width()
            ax.annotate("{}".format(h), xy=(bar.get_x() + w / 2, h), xytext=(0, 3),
                        textcoords="offset points", ha="center", va="bottom")
    auto_label(r1)
    auto_label(r2)
    auto_label(r3)

    figure.tight_layout()
    figure.savefig("figures/vulnerable_configurations.png", format="png")
    figure.savefig("figures/vulnerable_configurations.eps", format="eps", transparent=True)
    plt.show()


# Utility method used to copy the attacks from a first db file to a second
def merge_files(first_name, second_name, attack):
    first_db = FacebookDomains(first_name)
    second_db = FacebookDomains(second_name)
    for domain in first_db.get_attack_domains():
        first_fb = get_facebook(domain)
        second = second_db.get(Query().domain == domain["domain"])
        second_fb = get_facebook(second)
        if f"vulnerable_{attack}" in first_fb:
            second_fb[f"vulnerable_{attack}"] = first_fb[f"vulnerable_{attack}"]
        if f"authorization_response_{attack}" in first_fb:
            second_fb[f"authorization_response_{attack}"] = first_fb[f"authorization_response_{attack}"]
        second_db.update(second, doc_ids=[second.doc_id])


# Analyze the vulnerabilities in the different attack configurations
def analyze_configurations(domains):
    total = len(domains)
    table = [["a", "b", "c", "a \cup b \cup c"]]
    for scenario in range(0, 5):
        data = [str(scenario)]
        for config in ["a", "b", "c"]:
            vulnerable = len(get_vulnerable(domains, [f"{scenario}{config}"]))
            data.append(print_data(vulnerable, total))

        data.append(print_data(len(get_vulnerable(domains, get_attacks(str(scenario)))), total))
        table.append(data)

    # Add data related to all the attacks
    data = ["*"]
    for config in ["a", "b", "c"]:
        vulnerable = len(get_vulnerable(domains, get_attacks(config=config)))
        data.append(print_data(vulnerable, total))
    data.append(print_data(len(get_vulnerable(domains)), total))
    table.append(data)
    print(tabulate(table, headers="firstrow", tablefmt="latex"))


# Prin the flow type used
def print_flow_type():
    flows = [get_domain_flow(x).split(",")[0] for x in db.get_all()]
    counter = Counter(flows)
    table = [["Flow type", "Domains"]]
    for flow in counter.most_common():
        table.append([flow[0], print_data(flow[1], len(db.get_all()))])
    print(tabulate(table, headers="firstrow", tablefmt="latex"))
    print(f"Authorization code flow in {counter['code'] + counter['']} domains")
    print(f"Statistic generated considering {len(db.get_all())} domains")


def is_vulnerable_only(domain, config):
    scenarios = "0,1,2,3,4".split(",")
    config = set(config.split(","))
    facebook = get_facebook(domain)
    vulnerable = [facebook.get(f"vulnerable_{y}{x}") for x in config for y in scenarios
                  if is_vulnerable(domain, attacks=get_attacks(y))]
    other = [facebook.get(f"vulnerable_{y}{x}") for x in {"a", "b", "c"} - config for y in scenarios
             if is_vulnerable(domain, attacks=get_attacks(y))]

    print(f"{domain['domain']} ({config}) -> {bool(all(vulnerable) and not any(other))}")
    return len(vulnerable) > 0 and all(vulnerable) and not any(other)


def get_vulnerable_only(domains, attack, config):
    return [x for x in domains if is_vulnerable_only(x, config)]


def configurations_analysis(domains):
    scenarios = ["0", "1", "2", "3", "4"]
    configurations = ["a", "b", "c", "a,b", "a,c", "b,c", "a,b,c"]
    count = defaultdict(int)

    table = [["Configuration"] + scenarios + ["count"]]
    for configuration in configurations:
        data = [configuration]
        for scenario in scenarios:
            attacks = get_attacks(scenario, configuration)
            vulnerable = get_vulnerable_only(domains, scenario, configuration)
            data.append(len(vulnerable))
            print(f"Attacks: {attacks}, vulnerable: {len(vulnerable)}")
            count[configuration] += len(vulnerable)
        data.append(count[configuration])
        table.append(data)
    print(tabulate(table, headers="firstrow", tablefmt="github"))

    V = venn3(subsets=(7, 14, 31, 0, 2, 9, 48), set_labels=('Group A', 'Group B', 'Group C'), alpha=0.5)
    plt.show()


def main():
    print("Analysis functions")
    # domains = db.get_attack_domains(state=True)


if __name__ == "__main__":
    main()
