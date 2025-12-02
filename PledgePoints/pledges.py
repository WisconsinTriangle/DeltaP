import pandas as pd
from matplotlib import pyplot as plt
from pandas import DataFrame
import seaborn as sns

from PledgePoints.sqlutils import DatabaseManager


def get_pledge_points(db_manager: DatabaseManager) -> DataFrame:
    """
    Fetches and processes approved pledge points data from the database.

    Retrieves only approved point entries and converts them into a pandas
    DataFrame for analysis. The data is sorted by time in descending order
    (most recent first).

    Args:
        db_manager: DatabaseManager instance for accessing the database

    Returns:
        DataFrame: A pandas DataFrame containing approved pledge points
        with columns ['Time', 'PointChange', 'Pledge', 'Brother', 'Comment'].
        Sorted by Time in descending order.
    """
    # Get approved points using the database manager
    approved_entries = db_manager.get_approved_points()

    # Convert PointEntry objects to DataFrame
    data = []
    for entry in approved_entries:
        data.append(
            {
                "Time": entry.time,
                "PointChange": entry.point_change,
                "Pledge": entry.pledge,
                "Brother": entry.brother,
                "Comment": entry.comment,
            }
        )

    df = pd.DataFrame(data)

    # Handle empty dataframe case
    if df.empty:
        return df

    # Ensure Time is datetime and sort
    df["Time"] = pd.to_datetime(df["Time"])
    df = df.sort_values(by="Time", ascending=False)
    return df


def rank_pledges(df: DataFrame) -> pd.Series:
    """
    Ranks pledges by the sum of associated point changes in descending order.

    This function groups the provided DataFrame by the 'Pledge' column, sums the
    'PointChange' values for each group, and sorts the results in descending order of
    the summed values. The ranking highlights the pledges with the highest cumulative
    point changes.

    Args:
        df (DataFrame): Input DataFrame containing at least the following columns:
            - 'Pledge': Categorical or string column representing different pledge groups.
            - 'PointChange': Numeric column with values to be summed per group.

    Returns:
        pd.Series: A Series indexed by pledge, with values representing the cumulative
        point changes sorted in descending order.
    """
    return df.groupby("Pledge")["PointChange"].sum().sort_values(ascending=False)


def plot_rankings(rankings: pd.Series) -> str:
    """
    Generate a bar plot of rankings and save it as an image file.

    This function takes a pandas Series representing rankings data
    and creates a bar plot using the Seaborn library. The plot
    displays pledges on the x-axis and their corresponding total
    points on the y-axis. The function saves the plot to a PNG
    file named 'rankings.png' in the current directory and
    returns the filename.

    Args:
        rankings (pd.Series): A pandas Series object where the
            index represents the pledges and the values represent
            their corresponding total points.

    Returns:
        str: The filename of the saved bar plot image.
    """
    sns.set_theme(style="whitegrid")
    # Convert to DataFrame to ensure order is preserved and explicit
    df = rankings.reset_index()
    df.columns = ["Pledge", "TotalPoints"]
    # Sort explicitly in descending order
    df = df.sort_values("TotalPoints", ascending=False, ignore_index=True)
    # Use categorical ordering to ensure correct plotting order
    df["Pledge"] = pd.Categorical(df["Pledge"], categories=df["Pledge"], ordered=True)
    plt.figure(figsize=(max(6, len(df) * 0.7), 6))
    sns.barplot(x="Pledge", y="TotalPoints", data=df, order=df["Pledge"])
    plt.title("Pledge Rankings by Total Points")
    plt.xlabel("Pledge")
    plt.ylabel("Total Points")
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.tight_layout()
    plt.savefig("rankings.png")
    plt.close()
    return "rankings.png"
