# Active Directory

> [!NOTE]
> **Status**: Pending

---

> Microsoft's directory service for Windows domain networks, providing centralized authentication, authorization, and management of users, computers, and resources.

## Overview

| Property | Detail |
|---|---|
| Type | Directory Service / Identity Provider |
| Vendor | Microsoft |
| Protocol | LDAP, Kerberos, DNS, NTLM |
| Platforms | Windows Server |
| Website | https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview |

## Key Concepts

| Concept | Description |
|---|---|
| Domain | Logical group of network objects (users, computers, devices) |
| Forest | Collection of one or more domains sharing schema and global catalog |
| Tree | Hierarchy of domains sharing a contiguous namespace |
| OU (Organizational Unit) | Container for organizing objects within a domain |
| DC (Domain Controller) | Server that hosts AD DS and authenticates users |
| GPO (Group Policy Object) | Rules applied to users and computers in a domain |
| Schema | Defines object classes and attributes in AD |
| Global Catalog | Distributed data repository with partial attributes of all objects |

## Core Services

| Service | Description |
|---|---|
| AD DS | Active Directory Domain Services — core directory service |
| AD CS | Certificate Services — PKI infrastructure |
| AD FS | Federation Services — SSO across organizations |
| AD LDS | Lightweight Directory Services — LDAP without full AD DS |
| AD RMS | Rights Management Services — document protection |

## Authentication Protocols

| Protocol | Use Case |
|---|---|
| Kerberos | Default authentication in Windows domains (tickets) |
| NTLM | Legacy fallback authentication |
| LDAP | Directory queries and lookups |
| SAML / OAuth | Federation via AD FS |

## Common PowerShell Commands

```powershell
# Get domain info
Get-ADDomain

# List all users
Get-ADUser -Filter *

# Find user
Get-ADUser -Identity "jdoe" -Properties *

# Create user
New-ADUser -Name "John Doe" -SamAccountName "jdoe" -UserPrincipalName "jdoe@domain.com"

# List groups
Get-ADGroup -Filter *

# Add user to group
Add-ADGroupMember -Identity "GroupName" -Members "jdoe"

# List computers
Get-ADComputer -Filter *

# List OUs
Get-ADOrganizationalUnit -Filter *

# Get all GPOs
Get-GPO -All
```

## References

- [AD DS Overview](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview)
- [PowerShell AD Module](https://learn.microsoft.com/en-us/powershell/module/activedirectory/)
- [Kerberos Authentication](https://learn.microsoft.com/en-us/windows-server/security/kerberos/kerberos-authentication-overview)