class UserModel {
  final int userId;
  final String? googleSub;
  final String fullName;
  final String email;
  final String? profilePicture;
  final String authProvider;

  UserModel({
    required this.userId,
    required this.googleSub,
    required this.fullName,
    required this.email,
    required this.profilePicture,
    required this.authProvider,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      userId: json['user_id'],
      googleSub: json['google_sub'],
      fullName: json['full_name'] ?? '',
      email: json['email'] ?? '',
      profilePicture: json['profile_picture'],
      authProvider: json['auth_provider'] ?? 'google',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'google_sub': googleSub,
      'full_name': fullName,
      'email': email,
      'profile_picture': profilePicture,
      'auth_provider': authProvider,
    };
  }
}