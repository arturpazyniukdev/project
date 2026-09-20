from datetime import datetime
import os
from account import AccountStatus
from audit import AuditLog
from bank import Bank
from currency import Currency, convert
from risk import RiskLevel
from validators import ensure_text
import json
import csv
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter


class ReportBuilder:
    SKIPPED_ACCOUNT_FIELDS = ("history", "operations")

    def __init__(self, bank, audit_log) -> None:
        if not isinstance(bank, Bank):
            raise TypeError()

        self._bank = bank

        if not isinstance(audit_log, AuditLog):
            raise TypeError()

        self._audit_log = audit_log

    def build_client_report(self, client_id):
        client_id = ensure_text(client_id, "client_id")
        client = self._bank.get_client(client_id)

        accounts = []
        account_ids = self._bank.get_client_account_ids(client_id)
        total = 0
        currency = Currency.USD

        for account_id in account_ids:
            account = self._bank.get_account(account_id)
            if account.status is not AccountStatus.CLOSED:
                total += convert(account.balance, account.currency, currency)
            accounts.append(
                {
                    **account.get_account_info(),
                    "history": [
                        {**p, "at": p["at"].isoformat()} for p in account.history
                    ],
                    "operations": [
                        e.get_info()
                        for e in self._audit_log.get_entries(
                            account_id=account.account_id
                        )
                    ],
                }
            )

        return {
            "client": {
                "full_name": client.full_name,
                "client_id": client.client_id,
                "status": client.status.value,
                "phone": client.phone,
                "email": client.email,
                "birth_date": client.birth_date.isoformat(),
            },
            "accounts": accounts,
            "total": round(total, 2),
            "currency": currency.value,
            "generated_at": datetime.now().isoformat(),
        }

    def build_bank_report(self):
        total_accounts = 0
        total_clients = len(self._bank.get_clients())
        accounts_by_status = {}
        accounts_by_type = {}
        currency = Currency.USD

        for account in self._bank.get_accounts():
            total_accounts += 1
            status = account.status.value
            if status in accounts_by_status:
                accounts_by_status[status] += 1
            else:
                accounts_by_status[status] = 1

            account_type = type(account).__name__

            if account_type in accounts_by_type:
                accounts_by_type[account_type] += 1
            else:
                accounts_by_type[account_type] = 1

        return {
            "clients_ranking": self._bank.get_clients_ranking(currency),
            "accounts_by_status": accounts_by_status,
            "accounts_by_type": accounts_by_type,
            "total_accounts": total_accounts,
            "total_clients": total_clients,
            "total": self._bank.get_total_balance(currency),
            "currency": currency.value,
            "generated_at": datetime.now().isoformat(),
        }

    def build_risk_report(self):
        total_operations = 0
        by_risk_level = {}
        suspicious = []

        for entry in self._audit_log.get_entries():
            total_operations += 1
            level = entry.risk_level.value
            by_risk_level[level] = by_risk_level.get(level, 0) + 1

            if entry.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM):
                suspicious.append(entry.get_info())

        return {
            "total_operations": total_operations,
            "by_risk_level": by_risk_level,
            "suspicious": suspicious,
            "generated_at": datetime.now().isoformat(),
        }

    def build_account_rows(self):
        accounts = self._bank.get_accounts()

        rows = []
        for account in accounts:
            client = self._bank.get_client(account.client_id)
            row = {
                "client_full_name": client.full_name,
                "client_status": client.status.value,
                **account.get_account_info(),
                "account_type": type(account).__name__,
            }
            portfolio = row.pop("portfolio", None)
            if portfolio is not None:
                for asset, amount in portfolio.items():
                    row[f"portfolio_{asset}"] = amount

            rows.append(row)

        return rows

    def build_client_rows(self):
        clients = self._bank.get_clients()
        currency = Currency.USD

        rows = []

        for client in clients:
            total_balance = 0
            for account_id in client.account_ids:
                account = self._bank.get_account(account_id)
                if account.status is not AccountStatus.CLOSED:
                    total_balance += convert(
                        account.balance, account.currency, currency
                    )

            row = {
                "full_name": client.full_name,
                "client_id": client.client_id,
                "status": client.status.value,
                "phone": client.phone,
                "email": client.email,
                "birth_date": client.birth_date.isoformat(),
                "age": client.age,
                "account_count": len(client.account_ids),
                "total_balance": round(total_balance, 2),
                "currency": currency.value,
            }
            rows.append(row)

        return rows

    def export_to_json(self, report, path):
        if not isinstance(report, dict):
            raise TypeError()

        path = ensure_text(path, "path")

        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(report) + "\n")

    def export_to_csv(self, rows, path):
        if not isinstance(rows, list):
            raise TypeError(f"rows must be a list, got {type(rows).__name__}")

        for row in rows:
            if not isinstance(row, dict):
                raise TypeError(f"each row must be a dict, got {type(row).__name__}")

        path = ensure_text(path, "path")

        if not rows:
            return

        fields = {}
        for row in rows:
            fields.update(dict.fromkeys(row))

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(fields), restval="")
            writer.writeheader()
            writer.writerows(rows)

    def render_client_report(self, report):
        if not isinstance(report, dict):
            raise TypeError()

        lines = ["CLIENT REPORT", ""]

        for k, v in report["client"].items():
            lines.append(f"{k:<12} {v}")

        lines.append("")
        lines.append("ACCOUNTS")

        for account in report["accounts"]:
            lines.append("")
            lines.append(f"  {account['account_id']}")
            for k, v in account.items():
                if k in self.SKIPPED_ACCOUNT_FIELDS or k == "account_id":
                    continue
                lines.append(f"    {k:<16} {v}")
            lines.append(f"    {'operations':<16} {len(account['operations'])}")

        lines.append("")
        lines.append(f"{'TOTAL':<12} {report['total']} {report['currency']}")
        lines.append(f"{'generated':<12} {report['generated_at']}")

        return "\n".join(lines)

    def render_bank_report(self, report):
        if not isinstance(report, dict):
            raise TypeError()

        lines = ["BANK REPORT", ""]

        lines.append(f"{'clients':<16} {report['total_clients']}")
        lines.append(f"{'accounts':<16} {report['total_accounts']}")
        lines.append(f"{'total':<16} {report['total']} {report['currency']}")

        lines.append("")
        lines.append("ACCOUNTS BY STATUS")
        for status, count in report["accounts_by_status"].items():
            lines.append(f"  {status:<16} {count}")

        lines.append("")
        lines.append("ACCOUNTS BY TYPE")
        for account_type, count in report["accounts_by_type"].items():
            lines.append(f"  {account_type:<16} {count}")

        lines.append("")
        lines.append("CLIENTS RANKING")
        for position, (full_name, balance) in enumerate(report["clients_ranking"], 1):
            lines.append(f"  {position:>2}. {full_name:<16} {balance:>10.2f}")

        lines.append("")
        lines.append(f"{'generated':<16} {report['generated_at']}")

        return "\n".join(lines)

    def render_risk_report(self, report):
        if not isinstance(report, dict):
            raise TypeError()

        lines = ["RISK REPORT", ""]

        lines.append(f"{'operations':<16} {report['total_operations']}")
        lines.append(f"{'suspicious':<16} {len(report['suspicious'])}")

        lines.append("")
        lines.append("BY RISK LEVEL")
        for level, count in report["by_risk_level"].items():
            lines.append(f"  {level:<16} {count}")

        lines.append("")
        lines.append("SUSPICIOUS OPERATIONS")
        for entry in report["suspicious"]:
            sender = entry["sender_id"] or "-"
            receiver = entry["receiver_id"] or "-"
            lines.append(
                f"  {entry['at']} | {entry['operation']:<18} | "
                f"{entry['amount']:>10.2f} {entry['currency']} | "
                f"{sender} -> {receiver} | {entry['risk_level']} | {entry['risk_reason']}"
            )

        lines.append("")
        lines.append(f"{'generated':<16} {report['generated_at']}")

        return "\n".join(lines)

    def build_risk_rows(self):
        return [entry.get_info() for entry in self._audit_log.get_entries()]

    def save_accounts_by_type_chart(self, path):
        path = ensure_text(path, "path")
        fig, ax = plt.subplots()

        by_type = {}

        for account in self._bank.get_accounts():
            name = type(account).__name__
            if name in by_type:
                by_type[name] += 1
            else:
                by_type[name] = 1

        ax.pie(list(by_type.values()), labels=list(by_type.keys()))

        fig.savefig(path)
        plt.close(fig)

    def save_clients_by_balance_chart(self, path):
        path = ensure_text(path, "path")

        keys = []
        values = []
        for k, v in self._bank.get_clients_ranking():
            keys.append(k)
            values.append(v)

        fig, ax = plt.subplots()
        ax.bar(keys, values)
        ax.set_title("Clients by balance")
        ax.set_ylabel("USD")
        fig.savefig(path)
        plt.close(fig)

    def save_account_balance_movement_chart(self, path, account_id):
        path = ensure_text(path, "path")
        account_id = ensure_text(account_id, "account_id")

        account = self._bank.get_account(account_id)

        x = []
        y = []

        for entry in account.history:
            x.append(entry["at"])
            y.append(entry["balance"])

        fig, ax = plt.subplots()
        ax.plot(x, y, marker="o")
        ax.set_title("Balance movement")
        ax.set_ylabel("USD")
        ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
        fig.savefig(path)
        plt.close(fig)

    def save_charts(self, directory, account_id):
        directory = ensure_text(directory, "directory")
        os.makedirs(directory, exist_ok=True)

        self.save_accounts_by_type_chart(directory + "/accounts_by_type.png")
        self.save_clients_by_balance_chart(directory + "/clients_by_balance.png")
        self.save_account_balance_movement_chart(
            directory + "/balance_movement.png", account_id
        )
