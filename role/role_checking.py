import discord


async def check_eboard_role(interaction: discord.Interaction) -> bool:
    """

    Author: Warner

    Checks if the user who triggered the interaction has the "Executive Board" role

    :param interaction: The interaction object representing the command or event in
        Discord. This is used to access details about the user and their roles.
    :type interaction: discord.Interaction
    :return: Returns ``True`` if the user has the "Executive Board" role; otherwise, sends
        an ephemeral message to the user and returns ``False``.
    :rtype: bool
    """
    vp_role: discord.role = discord.utils.get(
        interaction.guild.roles, name="Executive Board"
    )
    if vp_role is None or vp_role not in interaction.user.roles:
        return False
    return True


async def check_brother_role(interaction: discord.Interaction) -> bool:
    """

    Author: Warner

    Checks if the user who triggered the interaction has the "Brother" role.

    :param interaction: The interaction object representing the command or event in
        Discord. This is used to access details about the user and their roles.
    :type interaction: discord.Interaction
    :return: Returns ``True`` if the user has the "Brother" role; otherwise, sends
        an ephemeral message to the user and returns ``False``.
    :rtype: bool
    """
    brother_role: discord.role = discord.utils.get(
        interaction.guild.roles, name="Brother"
    )
    if brother_role is None or brother_role not in interaction.user.roles:
        return False
    return True


async def check_info_systems_role(interaction: discord.Interaction) -> bool:
    """

    Author: Warner

    Checks if the user associated with the given interaction has the "Info Systems" role within the guild.
    This function verifies if the role exists in the interaction's guild and ensures that the user has it
    assigned in their roles. Returns a boolean based on these checks.

    :param interaction: The interaction object from which the user's roles and the guild's roles are accessed.
    :type interaction: discord.Interaction
    :return: True if the user has the "Info Systems" role and the role exists within the guild; False otherwise.
    :rtype: bool
    """
    infosys_role: discord.role = discord.utils.get(
        interaction.guild.roles, id=1032306248235888762
    )
    if infosys_role is None or infosys_role not in interaction.user.roles:
        return False
    return True
